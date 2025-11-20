#!/bin/bash

# MongoDB connection details
MONGO_URI="mongodb://xsearch_user:FE37k4MUjkvJ@central-mongo-v60-01.qa2-sg.cld:27017,central-mongo-v60-02.qa2-sg.cld:27017/xsearch?connectTimeoutMS=30000&socketTimeoutMS=30000&readPreference=secondaryPreferred"

# Insert test data for searchTerm "eser"
mongosh "$MONGO_URI" --eval '
db.search_term_categories.insertOne({
  "searchTerm": "eser",
  "catalogCategories": [
    {
      "name": "Kulkas",
      "code": "KU-1000008"
    }
  ],
  "modelIdentifiedCategories": [
    {
      "name": "Personalized perfume",
      "code": "NI-1000006",
      "score": 95,
      "boostValue": 150
    },
    {
      "name": "Celebrity Fragrance",
      "code": "CE-1000023",
      "score": 92,
      "boostValue": 120
    },
    {
      "name": "Paket Parfum",
      "code": "PA-1000051",
      "score": 88,
      "boostValue": 110
    }
  ]
})
'

echo "✅ Test data inserted successfully!"

