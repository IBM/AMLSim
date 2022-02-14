CONFIG = {
    'general': {
        'simulation_name': 'sample',
        'total_steps': 100
    },
    'default': {

    },
    'input': {
        "directory": "paramFiles/small8",
        "schema": "schema.json",
        "accounts": "accounts.csv",
        "alert_patterns": "alertPatterns.csv",
        "normal_models": "normalModels.csv",
        "degree": "degree.csv",
        "transaction_type": "transactionType.csv",
        "is_aggregated_accounts": True
    },
    "temporal": {
        "directory": "tmp",
        "transactions": "transactions.csv",
        "accounts": "accounts.csv",
        "alert_members": "alert_members.csv",
        "normal_models": "normal_models.csv"
    },
    "graph_generator": {
        "degree_threshold": 3,
        "high_risk_countries": "",
        "high_risk_business": ""
    },
}