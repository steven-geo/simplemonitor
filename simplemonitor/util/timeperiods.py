"""Handle Time periods and maintenance windows"""

import calendar
import datetime
import time
from enum import Enum
from typing import List, cast

import arrow


class TimeType(Enum):
    """Valid types of Time Periods to be handled"""

    ALWAYS = 0  # specified times are meaningless
    NOT = 1  # not allowed between the specified times
    ONLY = 2  # only allowed between the specified times


class TimeHandler(Enum):
    """Handle time Periods"""

    def __init__(self) -> None:
        pass

    def setup(self) -> None:
        # Validate times_type
        _times_type = cast(
            str,
            self.get_config_option(
                "times_type",
                required_type="str",
                allowed_values=["always", "only", "not"],
                default="always",
            ),
        )
        self._times_type = TimeType.ALWAYS  # type: TimeType
        if _times_type == "always":
            self._times_type = TimeType.ALWAYS
        elif _times_type == "only":
            self._times_type = TimeType.ONLY
        elif _times_type == "not":
            self._times_type = TimeType.NOT
        else:
            raise ValueError("times_type is not recongnised: {}".format(_times_type))

        # Create Time Information keys
        self._time_info = (None,None,)  # type: Tuple[Optional[datetime.time], Optional[datetime.time]]
        if self._times_type in [
            TimeType.ONLY,
            TimeType.NOT,
        ]:
            time_lower = str(
                self.get_config_option("time_lower", required_type="str", required=True)
            )
            time_upper = str(
                self.get_config_option("time_upper", required_type="str", required=True)
            )
            try:
                time_lower_split = list(map(int, time_lower.split(":")))
                time_upper_split = list(map(int, time_upper.split(":")))
                time_info = [
                    datetime.time(time_lower_split[0], time_lower_split[1]),
                    datetime.time(time_upper_split[0], time_upper_split[1]),
                ]
                # Create concatenated datetime.time objects with the H:m info of lower,upper
                self._time_info = (time_info[0], time_info[1])
            except Exception as error:
                raise RuntimeError("error processing time limit definition") from error

        # Validate Days Information- convert all to int day of week
        # Input: 0-6, Monday-Sunday, Mon-Sun - output 0-6 only
        self._days = []
        _valid_days = list(
            list(range(0, 7)) + list(calendar.day_name) + list(calendar.day_abbr)
        )
        self._days = cast(
            List[int],
            self.get_config_option(
                "days",
                required_type="[int]",
                allowed_values=_valid_days,
                default=list(range(0, 7)),
            ),
        )
        for dowindex, dowval in enumerate(self._days):
            if not isinstance(dowval, int):
                try:
                    if len(dowval) > 3:  # Long Day name
                        self._days[dowindex] = time.strptime(dowval, "%A").tm_wday
                    elif len(dowval) > 1:  # Short Day name
                        self._days[dowindex] = time.strptime(dowval, "%a").tm_wday
                except Exception as error:
                    raise RuntimeError("Invalid day of week specified") from error

    def describe_times(self) -> str:
        """Return a string describing the times we're active."""
        if self._times_type == TimeType.ALWAYS:
            return "(always)"
        days_list = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if self._days != list(range(0, 7)):
            allowed_days = ", ".join([days_list[day] for day in sorted(self._days)])
        else:
            allowed_days = "any day"
        start, end = self._time_info
        if start is None or end is None:
            return "(misconfigured times)"
        message = "between {start} and {end} ({tz}) on {days}".format(
            start=start.strftime("%H:%M"),
            end=end.strftime("%H:%M"),
            days=allowed_days,
            tz=self._times_tz,
        )
        if self._times_type == TimeType.ONLY:
            return "only {}".format(message)
        return "any time except {}".format(message)

    def allowed_time(self) -> bool:
        """Check if now is an allowed time."""
        if self._times_type == TimeType.ALWAYS:
            return True
        if self._time_info[0] is not None and self._time_info[1] is not None:
            now = arrow.now(self._times_tz).time()
            in_time_range = self._time_info[0] <= now < self._time_info[1]
            if self._times_type == TimeType.ONLY:
                self.alerter_logger.debug("in_time_range: %s", in_time_range)
                return in_time_range
            if self._times_type == TimeType.NOT:
                self.alerter_logger.debug(
                    "in_time_range: %s (inverting due to TimePeriod.NOT)",
                    in_time_range,
                )
                return not in_time_range
        self.alerter_logger.error(
            "this should never happen! Unknown times_type in alerter"
        )
        return True

    def allowed_today(self) -> bool:
        """Check if today is an allowed day."""
        if arrow.now(self._times_tz).weekday() not in self._days:
            self.alerter_logger.debug("not allowed to alert today")
            return False
        return True

    def time_maintenance(self) -> bool:
        """Call allowed day/time functions and return a true if we should action"""
        if TimeHandler.allowed_today(self) and TimeHandler.allowed_time(self):
            return True
        return False
