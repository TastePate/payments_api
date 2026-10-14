def create_payment_schedule(amount: int, months: int) -> list[int]:
    every_month, mod = divmod(amount, months)
    schedule = []
    for month in range(months):
        if mod > 0:
            schedule.append(every_month + 1)
            mod -= 1
        else:
            schedule.append(every_month)
    return schedule