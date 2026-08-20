# Classification of the series returned by the REN API.
# The endpoint is called "production breakdown", but not everything
# in it is production - there is consumption, cross-border trade
# with Spain, and pumped storage.

RENEWABLE = "renewable"
NON_RENEWABLE = "non_renewable"
NOT_PRODUCTION = "not_production"
STORAGE = "storage"

SERIES_CATEGORY = {
    # Renewable production
    "Eólica": RENEWABLE,
    "Solar": RENEWABLE,
    "Hídrica": RENEWABLE,
    "Biomassa": RENEWABLE,
    "Ondas": RENEWABLE,

    # Non-renewable production (still production, just not clean)
    "Gás Natural": NON_RENEWABLE,
    "Carvão": NON_RENEWABLE,
    "Outra Térmica": NON_RENEWABLE,

    # Not production: demand and cross-border trade
    "Consumo": NOT_PRODUCTION,
    "Consumo + Armazenamento": NOT_PRODUCTION,
    "Importação": NOT_PRODUCTION,
    "Exportação": NOT_PRODUCTION,

    # Storage: uses energy now to give it back later
    "Bombagem": STORAGE,
    "Consumo Baterias": STORAGE,
    "Injeção de Baterias": STORAGE,
}