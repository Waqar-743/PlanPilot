import httpx
from backend.config.settings import settings


class HotelAgent:
    """
    Finds accommodations using the Amadeus Hotel API.
    Trigger: Called in parallel with the Flight_Agent.
    Required Input: {
        "destination": "City", "check_in": "YYYY-MM-DD",
        "check_out": "YYYY-MM-DD", "budget_level": "low/med/high"
    }
    """

    AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
    HOTEL_LIST_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    HOTEL_OFFERS_URL = "https://test.api.amadeus.com/v3/shopping/hotel-offers"

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
        raise Exception(f"Amadeus auth failed: {response.status_code}")

    async def _get_iata_code(self, city: str) -> str | None:
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://test.api.amadeus.com/v1/reference-data/locations",
                params={"subType": "CITY", "keyword": city, "page[limit]": 1},
                headers={"Authorization": f"Bearer {token}"}
            )
        if response.status_code == 200 and response.json().get("data"):
            return response.json()["data"][0]["iataCode"]
        return None

    async def search_hotels(
        self, destination: str, check_in: str, check_out: str, budget_level: str
    ) -> dict:
        if not self.api_key or self.api_key.startswith("your_"):
            return self._fallback_hotels(destination, check_in, check_out, budget_level)

        try:
            token = await self._get_token()
        except Exception as e:
            return {"error": str(e)}

        city_code = await self._get_iata_code(destination)
        if not city_code:
            return {"error": f"Could not find city code for '{destination}'"}

        ratings = {"low": [1, 2, 3], "med": [3, 4], "high": [4, 5]}.get(budget_level, [3, 4])

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.HOTEL_LIST_URL,
                params={
                    "cityCode": city_code,
                    "radius": 20,
                    "radiusUnit": "KM",
                    "ratings": ",".join(str(r) for r in ratings),
                    "hotelSource": "ALL",
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )

        if response.status_code != 200:
            return {"error": f"Hotel search failed ({response.status_code})", "details": response.text[:200]}

        hotel_list = response.json().get("data", [])[:10]

        if not hotel_list:
            return {
                "destination": destination,
                "hotels_found": 0,
                "hotels": [],
                "summary": f"No hotels found in {destination} matching your budget."
            }

        hotel_ids = [h["hotelId"] for h in hotel_list]

        offers = await self._get_hotel_offers(token, hotel_ids, check_in, check_out)

        hotels = []
        for hotel_data in hotel_list:
            hotel_id = hotel_data["hotelId"]
            hotel_offer = offers.get(hotel_id, {})

            hotel_info = {
                "name": hotel_data.get("name", "Unknown Hotel"),
                "hotel_id": hotel_id,
                "rating": hotel_data.get("rating", "N/A"),
                "location": {
                    "latitude": hotel_data.get("geoCode", {}).get("latitude"),
                    "longitude": hotel_data.get("geoCode", {}).get("longitude"),
                },
                "distance_km": hotel_data.get("distance", {}).get("value", "N/A"),
            }

            if hotel_offer:
                hotel_info.update({
                    "price_per_night": hotel_offer.get("price_per_night", "N/A"),
                    "total_price": hotel_offer.get("total_price", "N/A"),
                    "currency": hotel_offer.get("currency", "USD"),
                    "room_type": hotel_offer.get("room_type", "Standard"),
                    "available": True,
                })
            else:
                hotel_info["available"] = False

            hotels.append(hotel_info)

        available_hotels = [h for h in hotels if h.get("available")]
        available_hotels.sort(key=lambda x: float(x.get("total_price", "999999") or "999999"))

        budget_tag = self._assess_budget_fit(available_hotels, budget_level)

        return {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "hotels_found": len(available_hotels),
            "hotels": available_hotels[:5],
            "budget_assessment": budget_tag,
            "summary": self._build_summary(available_hotels, destination, budget_level),
        }

    async def _get_hotel_offers(self, token: str, hotel_ids: list, check_in: str, check_out: str) -> dict:
        offers = {}
        batch_size = 5

        for i in range(0, len(hotel_ids), batch_size):
            batch = hotel_ids[i:i + batch_size]
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        self.HOTEL_OFFERS_URL,
                        params={
                            "hotelIds": ",".join(batch),
                            "checkInDate": check_in,
                            "checkOutDate": check_out,
                            "adults": 1,
                            "roomQuantity": 1,
                            "currency": "USD",
                        },
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        for hotel in response.json().get("data", []):
                            hid = hotel.get("hotel", {}).get("hotelId")
                            if hid and hotel.get("offers"):
                                offer = hotel["offers"][0]
                                price = offer.get("price", {})

                                from datetime import datetime
                                try:
                                    d1 = datetime.strptime(check_in, "%Y-%m-%d")
                                    d2 = datetime.strptime(check_out, "%Y-%m-%d")
                                    nights = (d2 - d1).days or 1
                                except ValueError:
                                    nights = 1

                                total = float(price.get("total", 0))
                                offers[hid] = {
                                    "price_per_night": str(round(total / nights, 2)),
                                    "total_price": price.get("total", "N/A"),
                                    "currency": price.get("currency", "USD"),
                                    "room_type": offer.get("room", {}).get("typeEstimated", {}).get("category", "Standard"),
                                }
                except Exception:
                    continue

        return offers

    def _assess_budget_fit(self, hotels: list, budget_level: str) -> str:
        if not hotels:
            return "No available hotels found."

        available_priced = [h for h in hotels if h.get("price_per_night") and h["price_per_night"] != "N/A"]
        if not available_priced:
            return "Pricing not available for these hotels."

        cheapest_ppn = float(available_priced[0]["price_per_night"])

        if budget_level == "low":
            if cheapest_ppn <= 80:
                return "Great budget options available!"
            elif cheapest_ppn <= 150:
                return "Moderate pricing. Hostels or guesthouses may offer better rates."
            else:
                return "WARNING: Hotels are expensive here. Consider alternative accommodations."
        elif budget_level == "med":
            if cheapest_ppn <= 200:
                return "Good mid-range options available."
            else:
                return "Prices are on the higher side for this area."
        else:
            return "Luxury options available."

    def _build_summary(self, hotels: list, destination: str, budget_level: str) -> str:
        if not hotels:
            return f"No available hotels found in {destination}. Consider broadening your search."

        priced = [h for h in hotels if h.get("total_price") and h["total_price"] != "N/A"]
        if not priced:
            return f"Found {len(hotels)} hotels in {destination}, but pricing is not yet available."

        cheapest = priced[0]
        return (
            f"Found {len(hotels)} hotels in {destination}. "
            f"Best rate: ${cheapest['total_price']} total "
            f"(~${cheapest['price_per_night']}/night) at {cheapest['name']}. "
            f"Rating: {cheapest.get('rating', 'N/A')} stars."
        )


    def _fallback_hotels(self, destination, check_in, check_out, budget_level):
        price_ranges = {"low": ("$30", "$80"), "med": ("$80", "$200"), "high": ("$200", "$500+")}
        low, high = price_ranges.get(budget_level, ("$80", "$200"))
        return {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "hotels_found": 0,
            "hotels": [],
            "budget_assessment": f"Typical {budget_level}-budget hotels in {destination} range {low}-{high}/night.",
            "summary": (
                f"Hotel search for {destination}: "
                f"Expect {low}-{high} per night for {budget_level}-budget stays. "
                "Check Booking.com or Hotels.com for live availability and rates."
            ),
            "note": "Amadeus API key not configured. Showing general guidance."
        }


hotel_agent = HotelAgent()
