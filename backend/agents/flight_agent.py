import httpx
from backend.config.settings import settings


class FlightAgent:
    """
    Finds real-time flight options using the Amadeus API.
    Trigger: Called after confirming the destination.
    Required Input: {
        "origin": "City", "destination": "City",
        "departure_date": "YYYY-MM-DD", "return_date": "YYYY-MM-DD",
        "budget_level": "low/med/high"
    }
    """

    AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
    SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    IATA_URL = "https://test.api.amadeus.com/v1/reference-data/locations"

    def __init__(self):
        self.api_key = settings.AMADEUS_API_KEY
        self.api_secret = settings.AMADEUS_API_SECRET
        self._token = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        if response.status_code == 200:
            self._token = response.json()["access_token"]
            return self._token
        raise Exception(f"Amadeus auth failed: {response.status_code} - {response.text}")

    async def _get_iata_code(self, city: str) -> str | None:
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.IATA_URL,
                params={"subType": "CITY,AIRPORT", "keyword": city, "page[limit]": 1},
                headers={"Authorization": f"Bearer {token}"}
            )
        if response.status_code == 200 and response.json().get("data"):
            return response.json()["data"][0]["iataCode"]
        return None

    async def search_flights(
        self, origin: str, destination: str,
        departure_date: str, return_date: str, budget_level: str
    ) -> dict:
        if not self.api_key or self.api_key.startswith("your_"):
            return self._fallback_flights(origin, destination, departure_date, return_date, budget_level)

        try:
            token = await self._get_token()
        except Exception as e:
            return {"error": str(e)}

        origin_code = await self._get_iata_code(origin)
        dest_code = await self._get_iata_code(destination)

        if not origin_code:
            return {"error": f"Could not find airport code for '{origin}'"}
        if not dest_code:
            return {"error": f"Could not find airport code for '{destination}'"}

        max_results = {"low": 5, "med": 5, "high": 3}.get(budget_level, 5)
        cabin = {"low": "ECONOMY", "med": "ECONOMY", "high": "BUSINESS"}.get(budget_level, "ECONOMY")

        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": dest_code,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": 1,
            "travelClass": cabin,
            "max": max_results,
            "currencyCode": "USD",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.SEARCH_URL,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )

        if response.status_code != 200:
            return {
                "error": f"Flight search failed ({response.status_code})",
                "details": response.text[:200]
            }

        data = response.json()
        flights = []

        for offer in data.get("data", []):
            outbound = offer["itineraries"][0]
            inbound = offer["itineraries"][1] if len(offer["itineraries"]) > 1 else None

            flight_info = {
                "price": f"${offer['price']['total']}",
                "price_numeric": float(offer["price"]["total"]),
                "currency": offer["price"]["currency"],
                "outbound": self._parse_itinerary(outbound),
                "return": self._parse_itinerary(inbound) if inbound else None,
                "booking_class": cabin,
                "seats_remaining": offer.get("numberOfBookableSeats", "N/A"),
            }
            flights.append(flight_info)

        flights.sort(key=lambda x: x["price_numeric"])

        budget_tag = self._assess_budget_fit(flights, budget_level)

        return {
            "origin": f"{origin} ({origin_code})",
            "destination": f"{destination} ({dest_code})",
            "departure_date": departure_date,
            "return_date": return_date,
            "flights_found": len(flights),
            "flights": flights,
            "budget_assessment": budget_tag,
            "summary": self._build_summary(flights, origin, destination, budget_level),
        }

    def _parse_itinerary(self, itinerary: dict) -> dict:
        segments = itinerary.get("segments", [])
        if not segments:
            return {}

        first = segments[0]
        last = segments[-1]

        stops = []
        for seg in segments[1:]:
            stops.append(seg["departure"]["iataCode"])

        return {
            "departure": first["departure"]["iataCode"],
            "departure_time": first["departure"]["at"],
            "arrival": last["arrival"]["iataCode"],
            "arrival_time": last["arrival"]["at"],
            "duration": itinerary.get("duration", "N/A"),
            "stops": len(segments) - 1,
            "stop_cities": stops,
            "airline": first.get("carrierCode", "N/A"),
        }

    def _assess_budget_fit(self, flights: list, budget_level: str) -> str:
        if not flights:
            return "No flights found"

        cheapest = flights[0]["price_numeric"]
        if budget_level == "low":
            if cheapest <= 300:
                return "Great budget options available!"
            elif cheapest <= 500:
                return "Moderate prices. Consider flexible dates for better deals."
            else:
                return "WARNING: Flights are expensive for this route. Budget may need adjustment."
        elif budget_level == "med":
            if cheapest <= 600:
                return "Good mid-range options available."
            else:
                return "Prices are on the higher side. Flexible dates may help."
        else:
            return "Premium options available."

    def _build_summary(self, flights: list, origin: str, destination: str, budget_level: str) -> str:
        if not flights:
            return f"No flights found from {origin} to {destination}. Consider flexible dates."

        cheapest = flights[0]
        most_expensive = flights[-1]

        summary = (
            f"Found {len(flights)} flights from {origin} to {destination}. "
            f"Prices range from {cheapest['price']} to {most_expensive['price']}. "
        )

        nonstop = [f for f in flights if f["outbound"].get("stops", 1) == 0]
        if nonstop:
            summary += f"Non-stop options available from {nonstop[0]['price']}. "

        return summary

    def _fallback_flights(self, origin, destination, departure_date, return_date, budget_level):
        price_ranges = {"low": ("$150", "$400"), "med": ("$300", "$800"), "high": ("$600", "$2000")}
        low, high = price_ranges.get(budget_level, ("$300", "$800"))
        return {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "flights_found": 0,
            "flights": [],
            "budget_assessment": f"Typical {budget_level}-budget flights on this route range {low}-{high}.",
            "summary": (
                f"Flight search for {origin} to {destination}: "
                f"Typical {budget_level}-budget prices range {low}-{high}. "
                "Check Google Flights or Skyscanner for live pricing and booking."
            ),
            "note": "Amadeus API key not configured. Showing general guidance."
        }


flight_agent = FlightAgent()
