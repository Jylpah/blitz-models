import pytest  # type: ignore
from pathlib import Path
from typing import Tuple, Dict
import logging
from blitzmodels import Maps, MapMode, MapModeStr

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug


########################################################
#
# Test Plan
#
########################################################

# 1) Read legacy JSON format
# 2) Write new format
# 3) Read new format

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(__file__).parent

MAPS_JSON: str = "05_maps.json"
MAPS_JSON_OLD: str = "05_maps_old.json"
MAPS_YAML: str = "05_maps.yaml"

MAPS_LOCALIZATION_STRS: Dict[str, str] = {
    "#maps:desert_train:02_desert_train_dt/02_desert_train_dt.sc2": "Desert Sands",
    "#maps:karelia:17_karelia_ka/17_karelia_ka.sc2": "Rockfield",
    "#maps:erlenberg:03_erlenberg_er/03_erlenberg_er.sc2": "Middleburg",
    "#maps:karieri:23_karieri_kr/23_karieri_kr.sc2": "Copperfield",
    "#maps:mountain:21_mountain_mnt/21_mountain_mnt.sc2": "Black Goldville",
    "#maps:amigosville:05_amigosville_am/05_amigosville_am.sc2": "Falls Creek",
    "#maps:medvedkovo:04_medvedkovo_md/04_medvedkovo_md.sc2": "Dead Rail",
    "#maps:savanna:09_savanna_sv/09_savanna_sv.sc2": "Oasis Palms",
    "#maps:tutorial:15_ordeal_ord/15_ordeal_ord.sc2": "Proving Grounds",
    "#maps:rudniki:06_rudniki_rd/06_rudniki_rd.sc2": "Mines",
    "#maps:himmelsdorf:himmelsdorf/himmelsdorf.sc2": "Himmelsdorf",
    "#maps:fort:07_fort_ft/07_fort_ft.sc2": "Fort Despair",
    "#maps:port:port/port.sc2": "Port",
    "#maps:north:north/north.sc2": "North",
    "#maps:asia:10_asia_as/10_asia_as.sc2": "Lost Temple",
    "#maps:malinovka:12_malinovka_ma/12_malinovka_ma.sc2": "Winter Malinovka",
    "#maps:pliego:13_pliego_pl/13_pliego_pl.sc2": "Castilla",
    "#maps:Random:Random": "Random map",
    "#maps:ordeal:15_ordeal_ord/15_ordeal_ord.sc2": "Trial by Fire",
    "#maps:port:14_port_pt/14_port_pt.sc2": "Port Bay",
    "#maps:canal:18_canal_cn/18_canal_cn.sc2": "Canal",
    "#maps:himmelsdorf:19_himmelsdorf_hm/19_himmelsdorf_hm.sc2": "Himmelsdorf",
    "#maps:lake:20_lake_lk/20_lake_lk.sc2": "Mirage",
    "#maps:italy:22_italy_it/22_italy_it.sc2": "Vineyards",
    "#maps:milbase:24_milibase_mlb/24_milibase_mlb.sc2": "Yamato Harbor",
    "#maps:canyon:25_canyon_ca/25_canyon_ca.sc2": "Canyon",
    "#maps:rock:28_rock_rc/28_rock_rc.sc2": "Mayan Ruins",
    "#maps:skit:29_skit_sk/29_skit_sk.sc2": "Naval Frontier",
    "#maps:grossberg:30_grossberg_sh/30_grossberg_sh.sc2": "Dynasty's Pearl",
    "#maps:test:sea_of_ducks/sea_of_ducks.sc2": "World of Ducks",
    "#maps:lumber:31_lumber_lm/31_lumber_lm.sc2": "Alpenstadt",
    "#maps:faust:32_faust_fa_night/32_faust_fa_night.sc2": "Faust",
    "#maps:holmeisk:26_holmeisk_hk/26_holmeisk_hk.sc2": "Wasteland",
    "#maps:neptune:33_neptune_nt/33_neptune_nt.sc2": "Normandy",
    "#maps:forgecity:34_forgecity_fc/34_forgecity_fc.sc2": "New Bay",
    "#maps:lumber:31_lumber_lm_night/31_lumber_lm_night.sc2": "Horrorstadt",
    "#maps:rift:35_rift_rt/35_rift_rt.sc2": "Hellas",
    "#maps:moon:40_moon_mn/40_moon_mn.sc2": "Sea of Tranquility",
    "#maps:idle:08_idle_id/08_idle_id.sc2": "Yukon",
    "#maps:iceworld:41_iceworld_ic/41_iceworld_ic.sc2": "Everfrost",
    "#maps:plant:11_plant_pn/11_plant_pn.sc2": "Ghost Factory",
    "#maps:holland:16_holland_hl/16_holland_hl.sc2": "Molendijk",
    "#maps:desert_train_02:02_desert_train_dt/02_desert_train_dt.sc2": "Desert Sands - Town",
    "#maps:desert_train_03:02_desert_train_dt/02_desert_train_dt.sc2": "Desert Sands - Dunes",
    "#maps:medvedkovo_02:04_medvedkovo_md/04_medvedkovo_md.sc2": "Dead Rail - Valley",
    "#maps:medvedkovo_03:04_medvedkovo_md/04_medvedkovo_md.sc2": "Dead Rail - Railroad",
    "#maps:milbase_02:24_milibase_mlb/24_milibase_mlb.sc2": "Yamato Harbor - Battleship",
    "#maps:milbase_03:24_milibase_mlb/24_milibase_mlb.sc2": "Yamato Harbor - Hills",
    "#maps:milbase_04:24_milibase_mlb/24_milibase_mlb.sc2": "Yamato Harbor - Centre",
    "#maps:milbase_05:24_milibase_mlb/24_milibase_mlb.sc2": "Yamato Harbor - Dock",
    "#maps:amigosville_02:05_amigosville_am/05_amigosville_am.sc2": "Falls Creek - Bridge",
    "#maps:amigosville_03:05_amigosville_am/05_amigosville_am.sc2": "Falls Creek - Factory",
    "#maps:erlenberg_01:03_erlenberg_er/03_erlenberg_er.sc2": "Middleburg - Town",
    "#maps:erlenberg_02:03_erlenberg_er/03_erlenberg_er.sc2": "Middleburg - Hill",
    "#maps:neptune_01:33_neptune_nt/33_neptune_nt.sc2": "Normandy - Hills",
    "#maps:neptune_02:33_neptune_nt/33_neptune_nt.sc2": "Normandy - Beach",
    "#maps:canal_01:18_canal_cn/18_canal_cn.sc2": "Canal - Factory",
    "#maps:lumber_01:31_lumber_lm/31_lumber_lm.sc2": "Alpenstadt - Town",
    "#maps:rudniki_01:06_rudniki_rd/06_rudniki_rd.sc2": "Mines - Hill",
    "#maps:rudniki_02:06_rudniki_rd/06_rudniki_rd.sc2": "Mines - Village",
    "#maps:rudniki_03:06_rudniki_rd/06_rudniki_rd.sc2": "Mines - Centre",
}


MAPS = pytest.mark.datafiles(
    FIXTURE_DIR / MAPS_JSON,
    FIXTURE_DIR / MAPS_JSON_OLD,
    on_duplicate="overwrite",
)


@pytest.fixture
def maps_old() -> int:
    """number of maps 05_maps_old.json"""
    return 49


@pytest.fixture
def maps_new() -> int:
    """number of maps 05_maps.json and 05_maps.yaml"""
    return 52


@pytest.fixture
def maps_names_updated() -> int:
    """number of maps in 05_maps.yaml having their names updated from localization strigs"""
    return 51


@pytest.fixture
def maps_added_updated() -> Tuple[int, int]:
    return (3, 4)  # number changes: 05_maps_old.json vs maps 05_maps.json


@pytest.fixture
def localization_strs() -> Dict[str, str]:
    return MAPS_LOCALIZATION_STRS


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file,count",
    [(MAPS_JSON, 52), (MAPS_JSON_OLD, 49)],
)
@MAPS
async def test_1_import_export(
    datafiles: Path, tmp_path: Path, file: str, count: int
) -> None:
    maps: Maps | None
    maps_fn: Path = tmp_path / file
    assert maps_fn.is_file(), f"could not find maps file: {maps_fn}"
    assert (
        maps := await Maps.open_json(maps_fn)
    ) is not None, f"could not open maps from: {maps_fn}"

    assert (
        len(maps) == count
    ), f"could not import all maps: got {len(maps)}, expected {count}"

    maps_export_fn: Path = tmp_path / "maps-export.json"
    assert (
        await maps.save_json(maps_export_fn) > 0
    ), f"could not write maps to file: {maps_export_fn}"

    assert (
        maps := await Maps.open_json(maps_export_fn)
    ) is not None, f"could not open maps from: {maps_export_fn}"

    assert (
        len(maps) == count
    ), f"could not import all maps: got {len(maps)}, expected {count}"

    for key, map in maps.items():
        assert isinstance(key, int), f"imported map keys are not int, but {type(key)}"
        assert isinstance(
            map.id, int
        ), f"imported map.id are not int, but {type(map.id)}"


@pytest.mark.asyncio
@MAPS
async def test_2_update(
    tmp_path: Path, datafiles: Path, maps_added_updated: tuple[int, int]
) -> None:
    maps_old: Maps | None
    maps_new: Maps | None

    maps_old_fn: Path = tmp_path / MAPS_JSON_OLD

    assert (
        maps_old := await Maps.open_json(maps_old_fn)
    ) is not None, f"could not open maps from: {maps_old_fn.name}"

    maps_new_fn: Path = tmp_path / MAPS_JSON
    assert (
        maps_new := await Maps.open_json(maps_new_fn)
    ) is not None, f"could not open maps from: {maps_new_fn.name}"

    (added, updated) = maps_old.update(maps_new)

    assert maps_added_updated[0] == len(
        added
    ), f"could not import all maps: got {len(added)}, expected {maps_added_updated[0]}"

    assert (
        maps_added_updated[1] == len(updated)
    ), f"could not import all maps: got {len(updated)}, expected {maps_added_updated[0]}"


@pytest.mark.asyncio
async def test_3_mapmode() -> None:
    map_mode: MapMode
    map_mode_str: MapModeStr
    for map_mode in MapMode:
        map_mode_str = map_mode.toMapModeStr
        assert map_mode.name == map_mode_str.name, "conversion to MapModeStr"
        assert map_mode == map_mode_str.toMapMode, "conversion back to MapMode failed"


@pytest.mark.asyncio
@pytest.mark.datafiles(FIXTURE_DIR / MAPS_YAML, on_duplicate="overwrite")
async def test_4_open_yaml(
    datafiles: Path,
    maps_new: int,
    localization_strs: Dict[str, str],
    maps_names_updated: int,
) -> None:
    """Test for Maps.open_yaml()"""
    maps_yaml: Path = next(datafiles.iterdir())

    maps: Maps | None
    assert (
        maps := await Maps.open_yaml(maps_yaml)
    ) is not None, f"could not open maps from YAML file: {maps_yaml.name}"

    for key, map in maps.items():
        assert isinstance(key, int), f"imported map keys are not int, but {type(key)}"
        assert isinstance(
            map.id, int
        ), f"imported map.id are not int, but {type(map.id)}"

    assert (
        len(maps) == maps_new
    ), f"incorrect number of maps read from a YAML file: {len(maps)} != {maps_new}"

    assert (
        (updated := maps.add_names(localization_strs=localization_strs))
        == maps_names_updated
    ), f"incorrect number of names updated:  {updated} != {maps_names_updated}"
