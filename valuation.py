"""Editable judgement model, not a trained or verified market appraisal."""
import math


def buyer_offer(value, offer):
    if isinstance(offer, bool):
        raise ValueError("Enter a valid offer.")
    try:
        offer = float(offer)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid offer.")
    if not math.isfinite(offer) or not 0 <= offer <= 100000:
        raise ValueError("Enter an offer between ₹0 and ₹1,00,000.")
    price = int(value * 80 // 100)
    if value <= 0:
        raise ValueError("This bicycle has no sale valuation.")
    accepted = offer >= price
    message = (f"Your offer is too low. Please raise it to at least ₹{price:,.0f} to proceed."
               if not accepted else
               f"Your offer meets the price. The cycle's fixed sale price is ₹{price:,.0f}, even if you offered more. Contact the operator to confirm availability and arrange a viewing; no purchase has been completed.")
    return {"price_ok": accepted, "price": price, "offer": offer, "message": message}


def estimate(data):
    def number(name, low, high):
        value = data.get(name)
        if isinstance(value, bool):
            raise ValueError(f"Check {name}.")
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Enter a number for {name}.")
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be between {low} and {high}.")
        return value

    new = number("replacement", 1000, 100000)
    age = number("age", 0, 20)
    repair = number("repairs", 0, 100000)
    overhead = number("overhead", 0, 100000)
    quote = number("quote", 0, 100000)
    target = number("target", 1, 100000)
    for field in ("brand", "model", "specs", "size"):
        if not isinstance(data.get(field), str) or not 1 <= len(data[field].strip()) <= 200:
            raise ValueError(f"Enter {field} (up to 200 characters).")
    condition = data.get("condition")
    factors = {"excellent": 1.0, "good": .9, "fair": .75, "poor": .55}
    if condition not in factors:
        raise ValueError("Choose a cosmetic condition.")
    demand = data.get("demand")
    if demand not in ("standard", "limited", "unknown"):
        raise ValueError("Choose size demand.")
    for field in ("inspected", "ownership", "damage"):
        if not isinstance(data.get(field), bool):
            raise ValueError(f"Check {field}.")
    retention = .85 - .10 * age if age <= 1 else max(.25, .75 * .88 ** (age - 1))
    size_factor = .9 if demand == "limited" else 1.0
    aged = new * retention
    cosmetic = aged * factors[condition]
    before_repairs = cosmetic * size_factor
    raw = max(0, before_repairs - repair)
    value = int(math.floor(raw / 50) * 50)
    threshold = value * .6
    sell = int(math.floor(value * .8))
    buy_max = max(0, math.ceil(threshold) - 1)
    profit = round(sell - quote - repair - overhead, 2)
    business_max = min(buy_max, math.floor(sell - repair - overhead - target))
    reasons = []
    if value <= 0:
        reasons.append("Repairs consume the estimated value.")
    if quote >= threshold:
        reasons.append("Seller quote is not strictly below 60% of estimated value.")
    if profit < target:
        reasons.append("Estimated contribution is below your chosen minimum profit.")
    if not data["inspected"]:
        reasons.append("A test ride and mechanical inspection are still needed.")
    if not data["ownership"]:
        reasons.append("Ownership has not been confirmed.")
    if data["damage"]:
        reasons.append("Possible frame or fork damage: get a mechanic's assessment; do not buy yet.")
    if demand == "unknown":
        reasons.append("Confirm frame size and likely buyer fit before buying.")
    steps = [
        {"label": "Current new price for the same model / close equivalent", "value": new, "note": "Brand, frame material, wheel size, brakes and gears belong in this comparable. Do not add separate premiums for them."},
        {"label": f"Age retention · {retention:.1%}", "value": round(aged, 2), "note": "Judgement assumption: 85% at age zero, 75% at one year, then 12% depreciation per additional year, with a 25% floor before condition and repairs."},
        {"label": f"Cosmetic condition · {factors[condition]:.0%}", "value": round(cosmetic, 2), "note": "Excellent 100%, good 90%, fair 75%, poor 55%. Cosmetic wear only; mechanical work is costed separately."},
        {"label": f"Size / buyer-pool adjustment · {size_factor:.0%}", "value": round(before_repairs, 2), "note": "Standard demand 100%; limited buyer pool 90%. An editable hypothesis, not measured IIT Bombay sales data. Unknown size blocks buying."},
        {"label": "Deduct outstanding repairs", "value": round(raw, 2), "note": f"Subtract ₹{repair:,.0f} to estimate today's as-is value. Use a mechanic's quote, not a guessed repair bill."},
        {"label": "Round down to nearest ₹50", "value": value, "note": "This is V: the conservative as-is second-hand value used for both of your percentages. The 80% sale target remains conservative even if repaired before sale."},
    ]
    return {"value": value, "low": math.floor(value * .8 / 50) * 50, "high": math.ceil(value * 1.2 / 50) * 50,
            "threshold": threshold, "buy_max": buy_max, "sell": sell, "profit": profit,
            "business_max": business_max if business_max >= 0 else None,
            "quote": quote, "repairs": repair, "overhead": overhead, "target": target,
            "eligible": not reasons, "reasons": reasons, "steps": steps,
            "margin": round(profit / sell * 100, 1) if sell else None}
