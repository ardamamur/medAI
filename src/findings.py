import spacy
import streamlit
import json


class FindingsExtractor:
    def __init__(self, st: streamlit):
        self.st = st
        self.st.title("Findings from Radiology Reports")
        self.st.markdown("Input a radiology report to extract medical entities in a structured form.", unsafe_allow_html=True)
        self.report_text = self.st.text_area("Radiology Report", height=300)
        self.extract_button = self.st.button("Extract Findings")
        self.nlp = spacy.load("en_core_web_sm")


    def extract_entities(self, report):
        # Load the spacy model    
        doc = self.nlp(report)
        entities = []
        for ent in doc.ents:
            entities.append({
                "original_term": ent.text,
                "mapped_term": ent.label_,
                "presence": True  # Assume presence for extracted entities
            })
        return entities

    def convert_to_json(self, entities):
        return json.dumps(entities, indent=4)

    def run(self):
        if self.extract_button:
            if self.report_text:
                entities = self.extract_entities(self.report_text)
                result_json = self.convert_to_json(entities)
                self.st.subheader("Extracted Entities")
                self.st.json(result_json)
            else:
                self.st.warning("Please input a radiology report.")





