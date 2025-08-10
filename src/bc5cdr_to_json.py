from bs4 import BeautifulSoup
from pathlib import Path
import json
import os

# import minidom for prettify xml
from xml.dom import minidom

class BC5CDR:
    def __init__(self, split:str):
        splits = {
            "train": Path("path\\to\\CDR_TrainingSet.BioC.xml"),
            "test": Path("path\\to\\CDR_TestSet.BioC.xml"),
            "dev": Path("path\\to\\CDR_DevelopmentSet.BioC.xml")
            }
        
        self.dataset_path = splits[split]
        with open(self.dataset_path, "r") as rx:
            self.xml_content = rx.read()
            

        self.soup = BeautifulSoup(self.xml_content, features="xml")
        self.output_save_path = Path("path\\to\\output\\folder") / f"{split}_set_preprocessed.json"
        self.output_save_path.parent.mkdir(parents=True, exist_ok=True)
        


    def prepare(self):
        # Lists all document tags
        self.documents = self.soup.find_all('document')
        # All documents are being added to this list. 
        self.records = []

        # add id of entities to map entities from entity-id to entity-name in relation tag
        entity_MESH_dictionary = self._make_entity_MESH_name_dictionary()
        
        passage_map = {0:'title', 1: 'abstract'}

        for document in self.documents:
            print(f"Processing {self.documents.index(document)}...")
            one_record = {
                "id": document.id.text
                }
            # Lists those two passeges existing in one document tag
            passages = document.find_all('passage')

            for passage in passages:
                # name of passage: title or abstract
                passage_name = passage_map[passages.index(passage)]

                # passage content
                passage_text = passage.find('text').text
                passage_offset = int(passage.offset.text)

                # add passage content to the one_record
                one_record[f'{passage_name}'] = passage_text

                # passage content entities
                annotations = passage.find_all("annotation")
                
                # put each annotation child in related list
                regular_annotations = []
                CompositeMention_annotations = []
                IndividualMention_annotations = []
                
                # spliting each annotation type: Regular, CompositeMention, IndividualMention
                for annotation in annotations:
                    if not annotation.find_all('infon', key='CompositeRole'):
                        regular_annotations.append(annotation)
                        continue
                    else:
                        if annotation.find_all('infon', key='CompositeRole')[0].text == "CompositeMention":
                            CompositeMention_annotations.append(annotation)
                            continue
                        else:
                            IndividualMention_annotations.append(annotation)
                            continue
                
                # will put passage entities in this list
                passage_entities = []

                # Regular annotations
                for regular_annotation in regular_annotations:
                    # ----- start of constructing regular annotation -----
                    # name
                    entity_name = regular_annotation.find('text').text
                    # type
                    entity_type = regular_annotation.find('infon', key='type').text
                    # MESH
                    entity_MESH = regular_annotation.find('infon', key='MESH').text.split("|")
                    # locations
                    locations_xml = regular_annotation.find_all("location")
                    locations_temp_list = []
                    for location in locations_xml:
                        entity_start_at = int(location['offset']) - passage_offset
                        entity_length = int(location['length'])
                        locations_temp_list.append([entity_start_at, entity_start_at + entity_length])
                    # ----- end of constructing regular annotation -----
                    one_annotation = {
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "entity_MESH": entity_MESH,
                        "entity_locations": locations_temp_list,
                        "IndividualMention": []
                    }
                    passage_entities.append(one_annotation)
                
                # IndividualMention annotations
                for CompositeMention_annotation in CompositeMention_annotations:
                    # ----- start of constructing IndividualMention annotation -----
                    # name
                    entity_name = CompositeMention_annotation.find('text').text
                    # type
                    entity_type = CompositeMention_annotation.find('infon', key='type').text
                    # MESH
                    entity_MESH = CompositeMention_annotation.find('infon', key='MESH').text.split("|")
                    # Locations
                    locations_xml = CompositeMention_annotation.find_all("location")
                    locations_temp_list = []
                    for location in locations_xml:
                        entity_start_at = int(location['offset']) - passage_offset
                        entity_length = int(location['length'])
                        locations_temp_list.append([entity_start_at, entity_start_at + entity_length])
                    
                    # will append individuals to this list
                    IndividualMentions = []
                    # IndividualMention
                    for IndividualMention_annotation in IndividualMention_annotations:
                        if IndividualMention_annotation.find('infon', key='MESH').text in entity_MESH:
                            # name
                            Individual_entity_name = IndividualMention_annotation.find('text').text
                            # type
                            Individual_entity_type = IndividualMention_annotation.find('infon', key='type').text
                            # MESH
                            Individual_entity_MESH = IndividualMention_annotation.find('infon', key='MESH').text.split("|")
                            # Locations
                            locations_xml = IndividualMention_annotation.find_all("location")
                            Individual_locations_temp_list = []
                            for location in locations_xml:
                                entity_start_at = int(location['offset']) - passage_offset
                                entity_length = int(location['length'])
                                Individual_locations_temp_list.append([entity_start_at, entity_start_at + entity_length])
                            one_Individual = {
                                "Individual_entity_name": Individual_entity_name,
                                "Individual_entity_type": Individual_entity_type,
                                "Individual_entity_MESH": Individual_entity_MESH,
                                "Individual_entity_locations": Individual_locations_temp_list,
                                }
                            IndividualMentions.append(one_Individual)
                            
                    # ----- end of constructing IndividualMention annotation -----
                    one_annotation = {
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "entity_MESH": entity_MESH,
                        "entity_locations": locations_temp_list,
                        "IndividualMention": IndividualMentions
                    }
                    passage_entities.append(one_annotation)
                one_record[f"{passage_name}_entities"] = passage_entities

            
            relations = document.find_all("relation")
            document_relations = []
            for relation in relations:
                relation_type = relation.find("infon", key="relation").text
                chemical_entity_MESH = relation.find("infon", key="Chemical").text
                disease_entity_MESH = relation.find("infon", key="Disease").text
                one_relation = {
                    "relation": relation_type,
                    "chemical": list(entity_MESH_dictionary[chemical_entity_MESH]),
                    "disease": list(entity_MESH_dictionary[disease_entity_MESH])
                }
                document_relations.append(one_relation)
            one_record["relations"] = document_relations
            self.records.append(one_record)
            os.system("cls")
        with open(self.output_save_path, "w", encoding="utf-8") as wj:
            json.dump(self.records, wj, ensure_ascii=False, indent=2)
            print(f"file saved at: {self.output_save_path}")






    def _make_entity_MESH_name_dictionary(self):
        # Lists all document tags
        self.documents = self.soup.find_all('document')
        # add id of entities to map entities from entity id to entity name in relation tag
        entity_MESH_dictionary = {}
        for document in self.documents:
            passages = document.find_all('passage')
            for passage in passages:
                annotations = passage.find_all("annotation")
                for annotation in annotations:
                    entity_name = annotation.find('text').text
                    entity_MESH = annotation.find('infon', key='MESH').text
                    entity_MESH_dictionary.setdefault(entity_MESH, set()).add(entity_name)
                    for mesh in entity_MESH.split("|"):
                        entity_MESH_dictionary.setdefault(mesh, set()).add(entity_name)
        return entity_MESH_dictionary
                
                
    
    def prettify_xml(self):
        dom = minidom.parseString(self.xml_content)
        ugly_pretty = dom.toprettyxml(indent="    ")
        pretty_xml = "\n".join([line for line in ugly_pretty.split("\n") if line.strip()])
        return pretty_xml


    

if __name__ == "__main__":
    
    # make instance
    bc5cdr = BC5CDR(split="train")
    # bc5cdr = BC5CDR(split="test")
    # bc5cdr = BC5CDR(split="dev")
    
    # # pretiffy
    # b = bc5cdr.prettify_xml()
    # xml_name = xml_path.name
    # pretty_xml_path = f"./Data/Prettified_{xml_name}"
    # FileUtils.write_file(path=pretty_xml_path, content=b)

    bc5cdr.prepare()



