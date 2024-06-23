import spacy
import json
nlp = spacy.load("en_core_web_sm")

def extract_entities(report):
    # Load the spacy model    
    doc = nlp(report)
    entities = []
    for ent in doc.ents:
        entities.append({
            "original_term": ent.text,
            "mapped_term": ent.label_,
            "presence": True  # Assume presence for extracted entities
        })
    return entities

def convert_to_json(entities):
    return json.dumps(entities, indent=4)
