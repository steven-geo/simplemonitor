"""Handle Time periods and maintenance windows"""

import arrow
import calendar

class TimeTypes(Enum):
    """Valid types of Time Periods to be handled"""
    ALWAYS = 0  # specified times are meaningless
    NOT = 1  # not allowed between the specified times
    ONLY = 2  # only allowed between the specified times

class TimeHandler(Enum):
    """Handle time Periods """

    def __init__(self,) -> None:
        pass

    def timestypevalidation(self, _times_type: str) -> None
        self._times_period = TimeTypes.ALWAYS  # type: TimeTypes
        if _times_type == "always":
            self._times_period = TimeTypes.ALWAYS
        elif _times_type == "only":
            self._times_period = TimeTypes.ONLY
        elif _times_type == "not":
            self._times_period = TimeTypes.NOT
        else:
            raise ValueError("times_type is not recongnised: {}".format(_times_type))

    def time_enabled(self) -> bool:
        """Call allowed day/time functions and return a true if we should action"""
        if self._allowed_today() and self._allowed_time():
            return True
        return False

    def _allowed_today(self) -> bool:
        """Check if today is an allowed day."""
        if arrow.now(self._times_tz).weekday() not in self._days:
            self.alerter_logger.debug("not allowed to alert today")
            return False
        return True

    def _allowed_time(self) -> bool:
        """Check if now is an allowed time."""
        if self._times_type == TimeTypes.ALWAYS:
            return True
        if self._time_info[0] is not None and self._time_info[1] is not None:
            now = arrow.now(self._times_tz).time()
            in_time_range = self._time_info[0] <= now < self._time_info[1]
            if self._times_type == self.ONLY:
                self.alerter_logger.debug("in_time_range: %s", in_time_range)
                return in_time_range
            if self._times_type == self.NOT:
                self.alerter_logger.debug(
                    "in_time_range: %s (inverting due to TimePeriod.NOT)",
                    in_time_range,
                )
                return not in_time_range
        self.alerter_logger.error(
            "this should never happen! Unknown times_type in alerter"
        )
        return True

    def createtimeinfo():
        self._time_info = (
            None,
            None,
        )  # type: Tuple[Optional[datetime.time], Optional[datetime.time]]
        if self._times_type in [AlertTimeFilter.ONLY, AlertTimeFilter.NOT]:
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

    def dowlistvalidate(self, _days: list):
        """Convert text day of week to int"""
        for dowindex, dowval in enumerate(_days):
            if not isinstance(dowval, int):
                try:
                    if len(dowval) > 3:
                        _days[dowindex] = time.strptime(dowval, "%A").tm_wday
                    elif len(downval) > 1:
                        _days[dowindex] = time.strptime(dowval, "%a").tm_wday
                except Exception as error:
                    raise RuntimeError("Invalid day of week specified") from error
        return _days

    def createdaysinfo():
        # Input: 0-6, Monday-Sunday, Mon-Sun - output 0-6 only
        _valid_days = list(range(0, 7) + list(calendar.day_name) + list(calendar.day_abbr))
        self._days = cast(
            List[int],
            self.get_config_option(
                "days",
                required_type="[int]",
                allowed_values=_valid_days,
                default=_valid_days,
            ),
        )
        self._days = dowlistvalidate(_days)
