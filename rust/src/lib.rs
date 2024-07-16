// NOTE: This is a python equivalent code to parse the uniprot xml file.
//
// from pathlib import Path
// from xml.sax import make_parser
// from xml.sax.handler import ContentHandler
//
// uniprot_file = Path("~/Downloads/uniprot_sprot.xml").expanduser()
// xmlparser = make_parser()
//
//
// class UniprotHandler(ContentHandler):
//     def __init__(self):
//         super().__init__()
//
//         self.current_context: list[str] = []
//
//         self._clean_entry()
//
//     def _clean_entry(self):
//         """
//         Clean up the entry information to start a new one.
//
//         Call this method when the end of an entry is reached.
//         """
//         self.accessions: list[str] = []
//         self.names: list[str] = []
//         self.protein_names: list[str] = []
//         self.gene_names: list[str] = []
//         self.organism_scientific: str | None = None
//         self.organism_commons: list[str] = []
//         self.organism_synonyms: list[str] = []
//         self.ncbi_taxonomy_id: str | None = None
//         self.lineage: list[str] = []
//         self.keywords: list[str] = []
//         self.geneontology_ids: list[str] = []
//         self.geneontology_names: list[str] = []
//         self.sequence: str | None = None
//
//     def _print_entry(self):
//         ic(self.accessions)
//         ic(self.names)
//         ic(self.protein_names)
//         ic(self.gene_names)
//         ic(self.organism_scientific)
//         ic(self.organism_commons)
//         ic(self.organism_synonyms)
//         ic(self.ncbi_taxonomy_id)
//         ic(self.lineage)
//         ic(self.keywords)
//         ic(self.geneontology_ids)
//         ic(self.geneontology_names)
//         ic(self.sequence)
//
//     @override
//     def startElement(self, name, attrs):
//         prev_len_context = len(self.current_context)
//         if self.current_context == ["uniprot", "entry", "organism"]:
//             if name == "name":
//                 if attrs.get("type") == "scientific":
//                     self.current_context.append("name-scientific")
//                 elif attrs.get("type") == "common":
//                     self.current_context.append("name-common")
//                 elif attrs.get("type") == "synonym":
//                     self.current_context.append("name-synonym")
//                 else:
//                     raise ValueError(f"Unknown name type: {attrs.get('type')}")
//             elif name == "dbReference" and attrs.get("type") == "NCBI Taxonomy":
//                 self.ncbi_taxonomy_id = attrs["id"]
//         elif self.current_context == ["uniprot", "entry"]:
//             if name == "dbReference" and attrs.get("type") == "GO":
//                 self.current_context.append("dbReference-GO")
//                 self.geneontology_ids.append(attrs["id"])
//         elif self.current_context == ["uniprot", "entry", "dbReference-GO"]:  # noqa: SIM102
//             if (name == "property"
//                 and attrs.get("type") == "term"
//             ):
//                 self.geneontology_names.append(attrs["value"])
//
//         if len(self.current_context) == prev_len_context:
//             # If the context did not change, add the new element to the context
//             self.current_context.append(name)
//
//     @override
//     def endElement(self, name):
//         assert self.current_context.pop().split("-")[0] == name
//         if name == "entry":
//             self._print_entry()
//             self._clean_entry()
//
//     @override
//     def characters(self, content):
//         # print(self.current_context)
//         match self.current_context:
//             case ["uniprot", "entry", "accession"]:
//                 self.accessions.append(content)
//             case ["uniprot", "entry", "name"]:
//                 self.names.append(content)
//             case ["uniprot", "entry", "gene", "name"]:
//                 self.gene_names.append(content)
//             case ["uniprot", "entry", "organism", "name-scienfitic"]:
//                 assert self.organism_scientific is None
//                 self.organism_scientific = content
//             case ["uniprot", "entry", "organism", "name-common"]:
//                 self.organism_commons.append(content)
//             case ["uniprot", "entry", "organism", "name-synonym"]:
//                 self.organism_synonyms.append(content)
//             case ["uniprot", "entry", "organism", "lineage", "taxon"]:
//                 self.lineage.append(content)
//             case ["uniprot", "entry", "keyword"]:
//                 self.keywords.append(content)
//             case (
//                 [
//                     "uniprot",
//                     "entry",
//                     "protein",
//                     "recommendedName",
//                     "fullName",
//                 ]
//                 | [
//                     "uniprot",
//                     "entry",
//                     "protein",
//                     "alternativeName",
//                     "fullName",
//                 ]
//             ):
//                 self.protein_names.append(content)
//             case ["uniprot", "entry", "sequence"]:
//                 self.sequence = content
//
//
// handler = UniprotHandler()
// xmlparser.setContentHandler(handler)
// xmlparser.parse(str(uniprot_file))

#[macro_use]
extern crate icecream;
extern crate shellexpand;

use pyo3::prelude::*;
use quick_xml::events::attributes::Attributes;
use quick_xml::events::Event;
use quick_xml::reader::Reader;
use sqlx::postgres::PgPoolOptions;
use tokio::runtime::{Handle, Runtime};

fn attr_eq(attr: &Attributes, key: &[u8], value: &[u8]) -> bool {
    // Attributes is an iterator. We don't want to reuse it so we clone it.
    let mut attr = attr.clone();
    let mut next = attr.next();
    let mut attribute;

    while next.is_some() {
        attribute = next.as_ref().unwrap().as_ref().unwrap();
        if attribute.key.as_ref() == key {
            return attribute.value.as_ref() == value;
        }

        next = attr.next();
    }

    false
}

fn attr_get(attr: &Attributes, key: &[u8]) -> Option<String> {
    // Attributes is an iterator. We don't want to reuse it so we clone it.
    let mut attr = attr.clone();
    let mut next = attr.next();
    let mut attribute;

    while next.is_some() {
        attribute = next.as_ref().unwrap().as_ref().unwrap();
        if attribute.key.as_ref() == key {
            return Some(
                attribute
                    .value
                    .iter()
                    .map(|&b| b as char)
                    .collect::<String>(),
            );
        }

        next = attr.next();
    }

    None
}

fn attr_get_int(attr: &Attributes, key: &[u8]) -> Option<i32> {
    // Attributes is an iterator. We don't want to reuse it so we clone it.
    let mut attr = attr.clone();
    let mut next = attr.next();
    let mut attribute;

    while next.is_some() {
        attribute = next.as_ref().unwrap().as_ref().unwrap();
        if attribute.key.as_ref() == key {
            return Some(
                attribute
                    .value
                    .iter()
                    .map(|&b| b as char)
                    .collect::<String>()
                    .parse::<i32>()
                    .unwrap(),
            );
        }

        next = attr.next();
    }

    None
}

fn bytes_to_string(content: &[u8]) -> String {
    content.iter().map(|&b| b as char).collect::<String>()
}

struct UniprotInfo {
    accessions: Vec<String>,
    names: Vec<String>,
    protein_names: Vec<String>,
    gene_names: Vec<String>,
    organism_scientific: Option<String>,
    organism_commons: Vec<String>,
    organism_synonyms: Vec<String>,
    ncbi_taxonomy_id: Option<i32>,
    deargen_ncbi_taxonomy_id: Option<i32>,
    lineage: Vec<String>,
    keywords: Vec<String>,
    geneontology_ids: Vec<String>,
    geneontology_names: Vec<String>,
    sequence: Option<String>,
    deargen_molecular_functions: Vec<String>, // deargen-curated molecular function
}

impl UniprotInfo {
    fn new() -> Self {
        Self {
            accessions: Vec::new(),
            names: Vec::new(),
            protein_names: Vec::new(),
            gene_names: Vec::new(),
            organism_scientific: None,
            organism_commons: Vec::new(),
            organism_synonyms: Vec::new(),
            ncbi_taxonomy_id: None,
            deargen_ncbi_taxonomy_id: None,
            lineage: Vec::new(),
            keywords: Vec::new(),
            geneontology_ids: Vec::new(),
            geneontology_names: Vec::new(),
            sequence: None,
            deargen_molecular_functions: Vec::new(),
        }
    }

    fn _clean_entry(&mut self) {
        self.accessions.clear();
        self.names.clear();
        self.protein_names.clear();
        self.gene_names.clear();
        self.organism_scientific = None;
        self.organism_commons.clear();
        self.organism_synonyms.clear();
        self.ncbi_taxonomy_id = None;
        self.deargen_ncbi_taxonomy_id = None;
        self.lineage.clear();
        self.keywords.clear();
        self.geneontology_ids.clear();
        self.geneontology_names.clear();
        self.sequence = None;
        self.deargen_molecular_functions.clear();
    }

    fn _print_entry(&self) {
        ice!(self.accessions);
        ice!(self.names);
        ice!(self.protein_names);
        ice!(self.gene_names);
        ice!(self.organism_scientific);
        ice!(self.organism_commons);
        ice!(self.organism_synonyms);
        ice!(self.ncbi_taxonomy_id);
        ice!(self.deargen_ncbi_taxonomy_id);
        ice!(self.lineage);
        ice!(self.keywords);
        ice!(self.geneontology_ids);
        ice!(self.geneontology_names);
        ice!(self.sequence);
        ice!(self.deargen_molecular_functions);
    }

    async fn sqlx_insert(
        &self,
        transaction: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        sqlx::query!(
            r#"
            INSERT INTO
              uniprot_info (
                accessions,
                names,
                protein_names,
                gene_names,
                organism_scientific,
                organism_commons,
                organism_synonyms,
                ncbi_taxonomy_id,
                deargen_ncbi_taxonomy_id,
                lineage,
                keywords,
                geneontology_ids,
                geneontology_names,
                sequence,
                deargen_molecular_functions
              )
            VALUES
              ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            "#,
            &self.accessions,
            &self.names,
            &self.protein_names,
            &self.gene_names,
            self.organism_scientific,
            &self.organism_commons,
            &self.organism_synonyms,
            self.ncbi_taxonomy_id,
            self.deargen_ncbi_taxonomy_id,
            &self.lineage,
            &self.keywords,
            &self.geneontology_ids,
            &self.geneontology_names,
            self.sequence,
            &self.deargen_molecular_functions
        )
        // In 0.7, `Transaction` can no longer implement `Executor` directly,
        // so it must be dereferenced to the internal connection type.
        .execute(&mut **transaction)
        .await?;

        Ok(())
    }

    /// Set the molecular functions from the uniport entry.
    fn curate_deargen_molecular_functions(&mut self) {
        if self.keywords.contains(&"Kinase".to_string()) {
            self.deargen_molecular_functions.push("Kinase".to_string());
        }

        for keyword in &self.keywords {
            if keyword.contains("Ion channel") {
                self.deargen_molecular_functions
                    .push("Ion channel".to_string());
                break;
            }
        }

        for keyword in &self.keywords {
            if keyword.contains("G-protein coupled receptor") {
                self.deargen_molecular_functions
                    .push("G-protein coupled receptor".to_string());
                break;
            }
        }

        if self.keywords.contains(&"Receptor".to_string()) {
            for geneontology_name in &self.geneontology_names {
                if geneontology_name.contains("estrogen receptor") {
                    self.deargen_molecular_functions
                        .push("Estrogen receptor".to_string());
                    break;
                }
            }
        }
    }

    fn curate_deargen_taxonomy_id(&mut self) {
        match self.organism_scientific.as_deref() {
            Some("Streptococcus pneumoniae serotype 4 (strain ATCC BAA-334 / TIGR4)") => {
                self.deargen_ncbi_taxonomy_id = Some(170187);
            }

            Some("Vibrio cholerae serotype O1 (strain ATCC 39315 / El Tor Inaba N16961)") => {
                self.deargen_ncbi_taxonomy_id = Some(243277);
            }

            Some("Cryptococcus neoformans var. neoformans serotype D (strain B-3501A) (Filobasidiella neoformans)") => {
                self.deargen_ncbi_taxonomy_id = Some(283643);
            }

            Some("Campylobacter jejuni subsp. jejuni serotype O:2 (strain ATCC 700819 / NCTC 11168)") => {
                self.deargen_ncbi_taxonomy_id = Some(32022);
            }

            Some("Oligotropha carboxidovorans (strain ATCC 49405 / DSM 1227 / KCTC 32145 / OM5)") => {
                self.deargen_ncbi_taxonomy_id = Some(504832);
            }

            Some("Listeria monocytogenes serovar 1/2a (strain ATCC BAA-679 / EGD-e)") => {
                self.deargen_ncbi_taxonomy_id = Some(169963);
            }

            Some("Yersinia pseudotuberculosis serotype I (strain IP32953)") => {
                self.deargen_ncbi_taxonomy_id = Some(273123);
            }

            Some("Vibrio cholerae serotype O1 (strain M66-2)") => {
                self.deargen_ncbi_taxonomy_id = Some(579112);
            }

            Some("Cryptococcus neoformans var. neoformans serotype D (strain JEC21 / ATCC MYA-565) (Filobasidiella neoformans)") => {
                self.deargen_ncbi_taxonomy_id = Some(214684);
            }

            Some("Human papillomavirus type 1 (Human papillomavirus type 1a)") => {
                self.deargen_ncbi_taxonomy_id = Some(2853106);
            }

            None => self.deargen_ncbi_taxonomy_id = None,

            organism => {
                let organism = organism.unwrap();

                if organism.contains("Human immunodeficiency virus type 1 group M subtype B") {
                    self.deargen_ncbi_taxonomy_id = Some(401671);
                } else if organism.contains("Hepatitis C virus") {
                    self.deargen_ncbi_taxonomy_id = Some(11103);
                } else if organism.contains("Human immunodeficiency virus 1") {
                    self.deargen_ncbi_taxonomy_id = Some(11676);
                } else if organism.contains("Bacillus megaterium") {
                    self.deargen_ncbi_taxonomy_id = Some(1138452);
                } else {
                    self.deargen_ncbi_taxonomy_id = self.ncbi_taxonomy_id;
                }
            }
        };
    }
}

async fn uniprot_xml_to_postgresql_async(
    uniprot_xml_path: String,
    uri: String,
) -> Result<(), Box<dyn std::error::Error>> {
    // PERF: quick-xml async 사용하면 더 느림. IO 퍼포먼스가 좋아서 그런듯.
    // 그리고 더 효율적으로 await을 안써야 하는데 시도는 안함.

    let uniprot_xml_path = shellexpand::tilde(&uniprot_xml_path).to_string();

    // let file = TokioFile::open(uniprot_file).await?;
    // let file = TokioBufReader::new(file);
    // let mut reader = Reader::from_reader(file);

    let mut reader = Reader::from_file(uniprot_xml_path)?;
    reader.config_mut().trim_text(true);

    let mut buf = Vec::new();

    let mut prev_len_context;
    let mut current_context: Vec<String> = Vec::new();

    let mut uniprot_info = UniprotInfo::new();

    // let conn_str =
    //     std::env::var("DATABASE_URL").expect("Env var DATABASE_URL is required for this example.");

    // create database if not exists
    // let pool = PgPoolOptions::new()
    //     .max_connections(5)
    //     .connect("postgresql://kiyoon:@localhost/uniprot")
    //     .await;
    //
    // if let Err(_e) = pool {
    //     //panic!("Error connecting to database: {:?}", e);
    //     let pool = PgPoolOptions::new()
    //         .max_connections(5)
    //         .connect("postgresql://kiyoon:@localhost")
    //         .await?;
    //     let _ = sqlx::query("CREATE DATABASE uniprot")
    //         .execute(&pool)
    //         .await?;
    // }

    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&uri)
        .await?;

    let mut transaction = pool.begin().await?;

    loop {
        match reader.read_event_into(&mut buf) {
            Err(e) => panic!("Error at position {}: {:?}", reader.buffer_position(), e),
            // exits the loop when reaching end of file
            Ok(Event::Eof) => break,

            // Some tags are self-closing without a value, so we need to handle them here.
            Ok(Event::Empty(event)) => {
                let attributes = event.attributes();
                match current_context.as_slice() {
                    [a, b, c] if a == "uniprot" && b == "entry" && c == "organism" => {
                        let tag_name = bytes_to_string(event.name().as_ref());
                        if tag_name == "dbReference"
                            && attr_eq(&attributes, b"type", b"NCBI Taxonomy")
                        {
                            uniprot_info.ncbi_taxonomy_id = attr_get_int(&attributes, b"id");
                        }
                    }
                    [a, b, c] if a == "uniprot" && b == "entry" && c == "dbReference-GO" => {
                        let attributes = event.attributes();
                        if event.name().as_ref() == b"property"
                            && attr_eq(&attributes, b"type", b"term")
                        {
                            uniprot_info
                                .geneontology_names
                                .push(attr_get(&attributes, b"value").unwrap());
                        }
                    }
                    _ => (),
                }
            }

            Ok(Event::Start(event)) => {
                prev_len_context = current_context.len();

                match current_context.as_slice() {
                    // ["uniprot", "entry", "organism"] => {
                    [a, b, c] if a == "uniprot" && b == "entry" && c == "organism" => {
                        let attributes = event.attributes();
                        if event.name().as_ref() == b"name" {
                            if attr_eq(&attributes, b"type", b"scientific") {
                                current_context.push("name-scientific".to_string());
                            } else if attr_eq(&attributes, b"type", b"common") {
                                current_context.push("name-common".to_string());
                            } else if attr_eq(&attributes, b"type", b"synonym") {
                                current_context.push("name-synonym".to_string());
                            } else {
                                panic!("Unknown name type: {:?}", attributes);
                            }
                        }
                    }
                    [a, b] if a == "uniprot" && b == "entry" => {
                        let attributes = event.attributes();
                        if event.name().as_ref() == b"dbReference"
                            && attr_eq(&attributes, b"type", b"GO")
                        {
                            current_context.push("dbReference-GO".to_string());
                            uniprot_info
                                .geneontology_ids
                                .push(attr_get(&attributes, b"id").unwrap());
                        }
                    }
                    _ => (),
                }

                if prev_len_context == current_context.len() {
                    // If the context did not change, add the new element to the context
                    let tag_name = bytes_to_string(event.name().as_ref());

                    current_context.push(tag_name.clone());
                }
            }

            Ok(Event::End(event)) => {
                let tag_name = bytes_to_string(event.name().as_ref());

                let popped = current_context.pop().unwrap();
                // the name can be modified to have suffixes like -scientific, -common, -synonym
                // so we need to compare with the first part of the name
                assert_eq!(
                    popped.split('-').next().unwrap(),
                    tag_name,
                    "Current context does not match tag name. Context: {:?}, Tag: {}",
                    current_context,
                    tag_name
                );

                if tag_name == "entry" {
                    uniprot_info.curate_deargen_molecular_functions();
                    uniprot_info.curate_deargen_taxonomy_id();
                    //uniprot_info._print_entry();

                    uniprot_info.sqlx_insert(&mut transaction).await?;

                    uniprot_info._clean_entry();
                }
            }

            Ok(Event::Text(content)) => match current_context.as_slice() {
                [a, b, c] if a == "uniprot" && b == "entry" && c == "accession" => {
                    uniprot_info.accessions.push(bytes_to_string(&content));
                }

                [a, b, c] if a == "uniprot" && b == "entry" && c == "name" => {
                    uniprot_info.names.push(bytes_to_string(&content));
                }
                [a, b, c, d] if a == "uniprot" && b == "entry" && c == "gene" && d == "name" => {
                    uniprot_info.gene_names.push(bytes_to_string(&content));
                }
                [a, b, c, d]
                    if a == "uniprot"
                        && b == "entry"
                        && c == "organism"
                        && d == "name-scientific" =>
                {
                    assert_eq!(uniprot_info.organism_scientific, None);
                    uniprot_info.organism_scientific = Some(bytes_to_string(&content));
                }
                [a, b, c, d]
                    if a == "uniprot" && b == "entry" && c == "organism" && d == "name-common" =>
                {
                    uniprot_info
                        .organism_commons
                        .push(bytes_to_string(&content));
                }
                [a, b, c, d]
                    if a == "uniprot" && b == "entry" && c == "organism" && d == "name-synonym" =>
                {
                    uniprot_info
                        .organism_synonyms
                        .push(bytes_to_string(&content));
                }
                [a, b, c, d, e]
                    if a == "uniprot"
                        && b == "entry"
                        && c == "organism"
                        && d == "lineage"
                        && e == "taxon" =>
                {
                    uniprot_info.lineage.push(bytes_to_string(&content));
                }
                [a, b, c] if a == "uniprot" && b == "entry" && c == "keyword" => {
                    uniprot_info.keywords.push(bytes_to_string(&content));
                }
                [a, b, c, d, e]
                    if a == "uniprot"
                        && b == "entry"
                        && c == "protein"
                        && (d == "recommendedName" || d == "alternativeName")
                        && e == "fullName" =>
                {
                    uniprot_info.protein_names.push(bytes_to_string(&content));
                }
                [a, b, c] if a == "uniprot" && b == "entry" && c == "sequence" => {
                    assert_eq!(uniprot_info.sequence, None);
                    uniprot_info.sequence = Some(bytes_to_string(&content));
                }
                _ => (),
            },

            // There are several other `Event`s we do not consider here
            _ => (),
        }
        buf.clear();
    }

    transaction.commit().await?;

    Ok(())
}

// https://stackoverflow.com/questions/68830056/the-proper-method-to-get-tokio-runtime-handle-based-on-current-running-environme
fn get_runtime_handle() -> (Handle, Option<Runtime>) {
    match Handle::try_current() {
        Ok(h) => (h, None),
        Err(_) => {
            let rt = Runtime::new().unwrap();
            (rt.handle().clone(), Some(rt))
        }
    }
}

fn uniprot_xml_to_postgresql_sync(
    uniprot_xml_path: String,
    uri: String,
) -> Result<(), Box<dyn std::error::Error>> {
    // Create the runtime
    //let rt = Runtime::new()?;
    // Spawn the root task

    // rt.block_on(async {
    //     uniprot_xml_to_postgresql_async(uniprot_file, uri).await?;
    // })

    let (handle, _rt) = get_runtime_handle();
    handle.block_on(async { uniprot_xml_to_postgresql_async(uniprot_xml_path, uri).await })
}

#[pyfunction]
fn uniprot_xml_to_postgresql(uniprot_xml_path: String, uri: String) -> PyResult<()> {
    let res = uniprot_xml_to_postgresql_sync(uniprot_xml_path, uri);

    if let Err(e) = res {
        Err(PyErr::new::<pyo3::exceptions::PyException, _>(format!(
            "{:?}",
            e
        )))
    } else {
        Ok(())
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn bio_data_to_db(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(uniprot_xml_to_postgresql, m)?)?;
    Ok(())
}
