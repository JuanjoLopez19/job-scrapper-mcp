from enum import StrEnum


class SupportedSites(StrEnum):
    LINKEDIN = "linkedin"
    INFO_EMPLEO = "infoempleo"
    TECNO_EMPLEO = "tecnoempleo"
    INDEED = "indeed"


SITE_DOMAINS: dict[SupportedSites, tuple[str, ...]] = {
    SupportedSites.LINKEDIN: ("linkedin.com",),
    SupportedSites.INFO_EMPLEO: ("infoempleo.com",),
    SupportedSites.TECNO_EMPLEO: ("tecnoempleo.com",),
    SupportedSites.INDEED: ("indeed.com",),
}
