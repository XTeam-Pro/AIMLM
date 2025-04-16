import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status

from app.api.dependencies.deps import CommittedSessionDep, UncommittedSessionDep, CurrentUser
from app.schemas.localization import TimeZoneCreate, TimeZoneUpdate, TimeZonePublic, TimeZonesCreateRequest
from app.core.postgres.dao import TimeZoneDAO


router = APIRouter(prefix="/timezones", tags=["timezones"])
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
@router.post("/", response_model=TimeZonePublic)
def create_timezone(
    tz_in: TimeZoneCreate,
    session: CommittedSessionDep,
    current_user: CurrentUser
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    dao = TimeZoneDAO(session)
    existing = dao.find_one_or_none({"name": tz_in.name})
    if existing:
        raise HTTPException(status_code=400, detail="TimeZone already exists")
    return dao.add(tz_in.model_dump())


test_timezones = { # Test time zones for insertion into a platform for API testing
    "timezones": [
        {"country": "Russia", "name": "Moscow Standard Time", "offset": "+03:00"},
        {"country": "Global", "name": "UTC", "offset": "+00:00"},
        {"country": "United Kingdom", "name": "GMT", "offset": "+00:00"},
        {"country": "The United States of America", "name": "Eastern Standard Time", "offset": "-05:00"},
        {"country": "The United States of America", "name": "Eastern Daylight Time", "offset": "-04:00"},
        {"country": "The United States of America", "name": "Central Standard Time", "offset": "-06:00"},
        {"country": "The United States of America", "name": "Central Daylight Time", "offset": "-05:00"},
        {"country": "The United States of America", "name": "Pacific Standard Time", "offset": "-08:00"},
        {"country": "The United States of America", "name": "Pacific Daylight Time", "offset": "-07:00"},
        {"country": "Australia", "name": "Australian Eastern Standard Time", "offset": "+10:00"},
        {"country": "Australia", "name": "Australian Eastern Daylight Time", "offset": "+11:00"},
        {"country": "United Kingdom", "name": "British Summer Time", "offset": "+01:00"},
        {"country": "France", "name": "Central European Time", "offset": "+01:00"},
        {"country": "France", "name": "Central European Summer Time", "offset": "+02:00"},
        {"country": "India", "name": "Indian Standard Time", "offset": "+05:30"},
        {"country": "Japan", "name": "Japan Standard Time", "offset": "+09:00"}
    ]
}
@router.post("/bulk", status_code=201)
def create_multiple_timezones(
    payload: TimeZonesCreateRequest,
    session: CommittedSessionDep
):
    """
    Bulk create timezones.
    """
    dao = TimeZoneDAO(session)

    try:
        created = dao.add_many(payload.timezones)
        return {
            "message": f"{len(created)} timezones created successfully",
            "items": [t.model_dump() for t in created]
        }
    except IntegrityError as ie:
        logger.error("Conflict with the database while inserting multiple timezones:", ie)
        raise HTTPException(status_code=400, detail="Something went wrong")
    except Exception as e:
        logger.error("Failed to insert multiple timezones:", e)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to insert timezones"
        )

@router.get("/", response_model=list[TimeZonePublic])
def list_timezones(session: UncommittedSessionDep, current_user: CurrentUser):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    dao = TimeZoneDAO(session)
    return dao.find_all()

@router.get("/{name}", response_model=TimeZonePublic)
def get_timezone(name: str, session: UncommittedSessionDep, current_user: CurrentUser):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    dao = TimeZoneDAO(session)
    tz = dao.find_one_or_none({"name": name})
    if not tz:
        raise HTTPException(status_code=404, detail="Timezone not found")
    return tz

@router.patch("/{name}", response_model=TimeZonePublic)
def update_timezone(
    name: str,
    tz_in: TimeZoneUpdate,
    session: CommittedSessionDep,
    current_user: CurrentUser
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    dao = TimeZoneDAO(session)
    db_tz = dao.find_one_or_none({"name": name})
    if not db_tz:
        raise HTTPException(status_code=404, detail="Timezone not found")
    return dao.update({"name": name}, tz_in.model_dump(exclude_unset=True))

@router.delete("/{name}")
def delete_timezone(name: str, session: CommittedSessionDep, current_user: CurrentUser):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    dao = TimeZoneDAO(session)
    tz = dao.find_one_or_none({"name": name})
    if not tz:
        raise HTTPException(status_code=404, detail="Timezone not found")
    dao.delete({"name": name})
    return {"detail": "Timezone deleted"}