MOCK_BERTHS_FILENAME = "tests/data/docks.csv"
MOCK_ANCHORAGES_FILENAME = "tests/data/anchorages.geojson"
MOCK_SECTIONS_FILENAME = "tests/data/sections.geojson"

MOCK_TRACES_FOLDERS = {
    "valid": "tests/data/traces/valid",
    "invalid": "tests/data/traces/invalid"
}

MOCK_SPAWN_FILENAME = "tests/data/spawn.geojson"

MOCK_BERTHS_COUNT = 2
MOCK_ANCHORAGES_COUNT = 1
SECONDS_IN_DAY = 86400

ANCHORAGE_DELAY = 100
TOTAL_EXPECTED_ANCHORAGE_DELAY = 2 * ANCHORAGE_DELAY
EXPECTED_TURNAROUND_TIME = 1000

TEST_RECEIVER = "test-destination"