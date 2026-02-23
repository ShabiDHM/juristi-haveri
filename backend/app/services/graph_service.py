# FILE: backend/app/services/graph_service.py
# PHOENIX PROTOCOL - GRAPH INTELLIGENCE V4.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Schema pivoted from Legal (Law/Claim) to Fiscal (Regulation/Transaction).
# 2. SEMANTIC: Entity labels updated for Audit and Accounting mapping.
# 3. LOGIC: Maintains robust Neo4j relationship mapping for financial forensic trails.
# 4. STATUS: 100% Accounting Aligned.

import os
import structlog
from neo4j import GraphDatabase, Driver, basic_auth
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = structlog.get_logger(__name__)

# Standard Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class GraphService:
    _driver: Optional[Driver] = None

    def _connect(self):
        if self._driver: return
        try:
            self._driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))
            self._driver.verify_connectivity()
        except Exception as e:
            logger.error(f"❌ Neo4j Connection Failed: {e}")
            self._driver = None

    def get_business_graph(self, business_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieves the fiscal relationship graph for a specific client/business."""
        self._connect()
        if not self._driver: return {"nodes": [], "links": []}
        
        nodes_dict = {}
        links_list = []
        
        # Note: case_id field name preserved in DB for infrastructural compatibility
        query = """
        MATCH (n) WHERE n.case_id = $business_id
        OPTIONAL MATCH (n)-[r]->(m) WHERE m.case_id = $business_id
        RETURN n, r, m
        """
        
        try:
            with self._driver.session() as session:
                res = session.run(query, business_id=business_id)
                for record in res:
                    n, r, m = record['n'], record['r'], record['m']
                    
                    for node in [n, m]:
                        if node:
                            n_id = str(node.element_id)
                            if n_id not in nodes_dict:
                                label = list(node.labels)[0] if node.labels else "FiscalEntity"
                                nodes_dict[n_id] = {
                                    "id": n_id,
                                    "name": node.get('name', 'N/A'),
                                    "group": label.upper(),
                                    "description": node.get('description', ''),
                                    # Highlight Transactions as primary nodes
                                    "val": 25 if label == "Transaction" else 15
                                }
                    
                    if r and n and m:
                        links_list.append({
                            "source": str(n.element_id),
                            "target": str(m.element_id),
                            "label": type(r).__name__
                        })
        except Exception as e:
            logger.error(f"Graph Fetch Error: {e}")
            
        return {"nodes": list(nodes_dict.values()), "links": links_list}

    def ingest_entities_and_relations(self, case_id: str, document_id: str, doc_name: str, entities: List[Dict], relations: List[Dict], doc_metadata: Optional[Dict] = None):
        """Ingests accounting entities and their fiscal relationships into the graph."""
        self._connect()
        if not self._driver: return

        def _tx_ingest(tx, c_id, d_id, d_name, ents, rels):
            # Record the financial document
            tx.run("MERGE (d:Document {id: $d_id}) SET d.case_id = $c_id, d.name = $d_name, d.processed_at = datetime()", d_id=d_id, c_id=c_id, d_name=d_name)
            
            for ent in ents:
                name = (ent.get("name") or ent.get("label") or "").strip()
                if not name: continue
                
                raw_type = str(ent.get("type", "Entity")).lower()
                
                # Pivot Legal mapping to Accounting labels
                if any(x in raw_type for x in ["claim", "transaction", "transaksion", "pagese"]): 
                    label = "Transaction"
                elif any(x in raw_type for x in ["law", "ligj", "rregullore", "regulation", "udhezim"]): 
                    label = "Regulation"
                elif any(x in raw_type for x in ["fact", "fakt", "entry", "regjistrim"]): 
                    label = "AccountingEntry"
                elif any(x in raw_type for x in ["evidence", "prove", "fature", "invoice", "vertetim"]): 
                    label = "AuditProof"
                else: 
                    label = "FiscalEntity"

                tx.run(f"""
                    MERGE (e:{label} {{name: $name, case_id: $c_id}})
                    SET e.description = $desc
                    WITH e
                    MATCH (d:Document {{id: $d_id}})
                    MERGE (d)-[:MENTIONS]->(e)
                """, name=name, c_id=c_id, d_id=d_id, desc=ent.get("description", ""))

            for rel in rels:
                subj = rel.get("source") or rel.get("subject")
                obj = rel.get("target") or rel.get("object")
                if subj and obj:
                    # Relationships: e.g., VERIFIES, BELONGS_TO, ACCORDING_TO
                    pred = str(rel.get("relation", "RELATED")).upper().replace(" ", "_")
                    tx.run(f"""
                        MATCH (a {{name: $subj, case_id: $c_id}}), (b {{name: $obj, case_id: $c_id}})
                        MERGE (a)-[:{pred} {{case_id: $c_id}}]->(b)
                    """, subj=subj, obj=obj, c_id=c_id)

        try:
            with self._driver.session() as session:
                session.execute_write(_tx_ingest, case_id, document_id, doc_name, entities, relations)
        except Exception as e:
            logger.error(f"Ingestion Error: {e}")

    def delete_node(self, node_id: str):
        self._connect()
        if not self._driver: return
        try:
            with self._driver.session() as session:
                session.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
        except Exception: pass

graph_service = GraphService()