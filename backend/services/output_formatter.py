import re
import json


class OutputFormatter:
    """
    Final quality control layer before the Root Agent speaks to the user.
    Prevents raw JSON leakage, enforces modality rules, and applies guardrails.
    """

    def format_response(self, text: str, modality: str) -> str:
        text = self._strip_raw_json(text)
        text = self._strip_agent_references(text)

        if modality == "voice":
            text = self._format_for_voice(text)
        else:
            text = self._format_for_text(text)

        return text.strip()

    # ------------------------------------------------------------------
    # Guardrail 1: No Hallucinations -- strip any leftover JSON blobs
    # ------------------------------------------------------------------
    def _strip_raw_json(self, text: str) -> str:
        json_block = re.compile(r'```json\s*\{.*?\}\s*```', re.DOTALL)
        text = json_block.sub('', text)

        orphan_json = re.compile(r'(?<!\w)\{["\'][\w_]+["\']:\s*["\'].*?\}', re.DOTALL)
        matches = orphan_json.findall(text)
        for match in matches:
            if len(match) > 200:
                text = text.replace(match, '')

        return text

    # ------------------------------------------------------------------
    # Guardrail 3: One Voice -- never expose agent internals
    # ------------------------------------------------------------------
    def _strip_agent_references(self, text: str) -> str:
        patterns = [
            (r'[Tt]he [Ff]light[_ ][Aa]gent\s+(said|returned|found|reported)', 'I found'),
            (r'[Tt]he [Hh]otel[_ ][Aa]gent\s+(said|returned|found|reported)', 'I found'),
            (r'[Tt]he [Ww]eather[_ ][Aa]gent\s+(said|returned|found|reported)', 'I checked'),
            (r'[Tt]he [Ll]ocal[_ ][Ee]xpert[_ ][Aa]gent\s+(said|returned|found|reported|built|created)', 'I planned'),
            (r'I am (talking to|contacting|querying|calling) the \w+ [Aa]gent', 'I\'m looking into that'),
            (r'[Ss]ub-?[Aa]gent', 'system'),
            (r'[Aa]gent-to-[Aa]gent', 'internal'),
            (r'A2A\s+(handoff|delegation|communication)', 'coordination'),
            (r'[Tt]he\s+[Ff]light[_ ]?[Aa]gent\s+said', 'I found that'),
            (r'[Tt]he\s+[Hh]otel[_ ]?[Aa]gent\s+said', 'I found that'),
            (r'[Tt]he\s+[Ww]eather[_ ]?[Aa]gent\s+said', 'I checked and'),
            (r'Weather[_ ]?Agent', 'weather check'),
            (r'Flight[_ ]?Agent', 'flight search'),
            (r'Hotel[_ ]?Agent', 'hotel search'),
            (r'Local[_ ]?Expert[_ ]?Agent', 'local planning'),
        ]
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    # ------------------------------------------------------------------
    # Text Mode Formatting
    # ------------------------------------------------------------------
    def _format_for_text(self, text: str) -> str:
        text = self._ensure_section_headers(text)
        text = self._format_prices_text(text)
        return text

    def _ensure_section_headers(self, text: str) -> str:
        section_keywords = {
            'weather': 'Weather Overview',
            'flight': 'Flights',
            'hotel': 'Accommodation',
            'accommodation': 'Accommodation',
            'itinerary': 'Itinerary',
            'day 1': 'Day 1',
        }
        return text

    def _format_prices_text(self, text: str) -> str:
        text = re.sub(r'(?<!\$)(\d{1,2},?\d{3})\s*(USD|dollars)', r'$\1', text)
        return text

    # ------------------------------------------------------------------
    # Voice Mode Formatting
    # ------------------------------------------------------------------
    def _format_for_voice(self, text: str) -> str:
        # Convert prices FIRST before stripping special chars
        text = self._convert_prices_to_spoken(text)
        text = re.sub(r'[*#_`~]', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'^\s*[-•]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def _convert_prices_to_spoken(self, text: str) -> str:
        def price_to_words(match):
            amount = match.group(1).replace(',', '')
            try:
                num = float(amount)
                if num == int(num):
                    return self._number_to_words(int(num)) + " dollars"
                else:
                    whole = int(num)
                    cents = int(round((num - whole) * 100))
                    result = self._number_to_words(whole) + " dollars"
                    if cents > 0:
                        result += " and " + self._number_to_words(cents) + " cents"
                    return result
            except ValueError:
                return match.group(0)

        text = re.sub(r'\$(\d[\d,]*\.?\d*)', price_to_words, text)
        return text

    def _number_to_words(self, n: int) -> str:
        if n == 0:
            return "zero"

        ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
                'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
                'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
        tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty',
                'sixty', 'seventy', 'eighty', 'ninety']

        if n < 0:
            return "negative " + self._number_to_words(-n)
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + ('' if n % 10 == 0 else '-' + ones[n % 10])
        if n < 1000:
            return ones[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + self._number_to_words(n % 100))
        if n < 1000000:
            return self._number_to_words(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + self._number_to_words(n % 1000))
        return str(n)

    # ------------------------------------------------------------------
    # Guardrail 2: Budget Adherence Check
    # ------------------------------------------------------------------
    def check_budget_adherence(self, flight_data: dict, hotel_data: dict, budget_level: str) -> str | None:
        warnings = []

        if not flight_data.get("error") and flight_data.get("flights"):
            cheapest_flight = flight_data["flights"][0].get("price_numeric", 0)
            if budget_level == "low" and cheapest_flight > 500:
                warnings.append(
                    f"Note: The cheapest flight I found is ${cheapest_flight:.0f}, "
                    "which is on the higher side for a budget trip. "
                    "Consider flexible dates or nearby airports for better deals."
                )
            elif budget_level == "med" and cheapest_flight > 1000:
                warnings.append(
                    f"Note: Flight prices start at ${cheapest_flight:.0f}, "
                    "which is above typical mid-range pricing for this route."
                )

        if not hotel_data.get("error") and hotel_data.get("hotels"):
            cheapest_hotel = hotel_data["hotels"][0]
            ppn = cheapest_hotel.get("price_per_night", "0")
            if ppn != "N/A":
                ppn_num = float(ppn)
                if budget_level == "low" and ppn_num > 100:
                    warnings.append(
                        f"Note: Hotels start at ${ppn_num:.0f}/night, "
                        "which is above typical budget range. "
                        "Consider hostels or guesthouses for more affordable options."
                    )
                elif budget_level == "med" and ppn_num > 250:
                    warnings.append(
                        f"Note: Hotel prices start at ${ppn_num:.0f}/night, "
                        "which is on the higher end for mid-range."
                    )

        if warnings:
            return "\n\n".join(warnings)
        return None

    # ------------------------------------------------------------------
    # Validate sub-agent data for errors (no-hallucination guardrail)
    # ------------------------------------------------------------------
    def build_error_notices(self, weather_data: dict, flight_data: dict, hotel_data: dict) -> list[str]:
        notices = []

        if weather_data.get("error"):
            notices.append(
                "I wasn't able to get the weather forecast for your destination. "
                "I'll plan the itinerary assuming typical seasonal conditions."
            )

        if flight_data.get("error"):
            notices.append(
                "I'm having trouble finding flights for those exact dates. "
                "Are you flexible by a day or two? That might help me find better options."
            )

        if hotel_data.get("error"):
            notices.append(
                "I couldn't find hotel availability for your dates. "
                "You might want to check closer to your travel date, or I can look at alternative areas."
            )

        return notices


output_formatter = OutputFormatter()
