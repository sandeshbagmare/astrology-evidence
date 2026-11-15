# Rule registry and knowledge model

Status: researched proposal, 2026-11-15. Documentation only; no executable rules, licensed verses, application code or tests were produced. This extends [domain](05-astrology-domain.md), [contracts](12-data-and-api-contracts.md), [domain research](18-domain-research-dossier.md), [editorial workflow](19-corpus-acquisition-and-editorial-playbook.md) and [evidence validation](26-evidence-validation-and-contradictions.md).

## Evidence-informed design

Use PostgreSQL tables and typed relation rows initially. A graph database adds no demonstrated benefit to the small reviewed corpus. W3C PROV-O distinguishes entities, activities and agents, and provides derivation, attribution and revision relations [S1]. Adopt those distinctions as a conceptual mapping: passage revisions and chart snapshots are entities; extraction, calculation and review are activities; reviewers and software services are agents. Provenance documents origin and responsibility; it does not establish truth.

SKOS supports concept schemes, language-tagged labels and mapping relations [S2]. Use this vocabulary discipline for retrieval and editorial navigation, without requiring an RDF store. A lexical match is not predicate equivalence. Do not infer doctrinal agreement from similar English labels or use a broad concept relation as an executable rule.

Three artifacts stay separate: deterministic computation produces chart facts under explicit conventions; a reviewed rule evaluates attributed conditions against those facts; narrative explains accepted facts and attributed teachings. The model may propose a candidate rule for editorial review but cannot publish, approve, evaluate or silently repair one.

## Typed ontology and relations

Retain existing SourceWork, Edition and Passage identities. A work names an intellectual attribution, possibly uncertain. An edition names a specific publication and rights record. A passage revision names exact text, checksum and coordinates. Its layer is `original`, `translation`, `commentary` or `modern_synthesis`; translator/commentator identity belongs to that layer. A translation is not silently promoted into the original author's wording.

Create versioned concept schemes with stable opaque concept IDs, preferred labels by language, alternate transliterations and scope notes. Concept types include `graha`, `rashi`, `bhava`, `dignity`, `aspect` and `school`. Graha identifiers preserve traditional vocabulary while recording whether their astronomical referent is a body or calculated point. Rashi and bhava are different types even when both use twelve ordinal positions. Dignity is a reviewed classification under a named table revision. Aspect names reference a specific algorithm/convention; sign-based and angular relationships cannot share an unlabeled predicate.

School/profile IDs bind chart type, zodiac, ayanamsha, house model, node mode and applicable rule-set revision. Different profiles require separate evaluation. Store `supports`, `qualifies`, `contradicts`, `derived_from`, `supersedes`, `equivalent_to` and `close_match` edges with typed endpoints, scope, reviewer and evidence. Editorial contradiction is scoped to comparable premises, source layer and conclusion. It is not simply opposite wording.

Use foreign keys for source links and typed endpoint validation for edges. PostgreSQL owns publication and rights status; Qdrant remains a rebuildable retrieval index. An optional future RDF export can map provenance and vocabulary terms, but do not advertise full PROV/SKOS conformance without checking mapping semantics.

## Rule revision contract

Each published revision is immutable. The logical rule ID groups revisions; every evaluation pins the exact revision and content hash.

| Field | Type and required invariant |
|---|---|
| `rule_id`, `revision_id` | Opaque IDs; revisions never overwrite prior content |
| `schema_version` | Supported schema identifier; unknown versions rejected |
| `revision_hash` | Digest of canonical content, including exception references |
| `source_links` | Nonempty edition-specific passage revision IDs, hashes and layers |
| `profile_id` | Exact reviewed school/convention profile revision |
| `chart_types` | Closed supported enum; MVP D1 only |
| `required_facts` | Typed dependencies, availability and stability requirements |
| `birth_precision_policy` | Accepted precision modes and forbidden time-sensitive dependencies |
| `condition` | Bounded, validated condition tree |
| `exceptions` | Explicit exception conditions plus completeness-review status |
| `result_template` | Attributed teaching; no computed values or promised outcomes |
| `review_state` | `draft`, `reviewed`, `executable`, `withdrawn` |
| `approvals` | Reviewer identity, role, decision, timestamp and revision hash |
| `relations` | Scoped supersession, conflict and equivalence edges |
| `rights_dependencies` | References checked at evaluation/publication/display |
| `effective_at` | UTC activation time; cannot replace revision provenance |
| `test_fixture_ids` | Positive, negative, boundary and unknown-input fixtures |

Concept values use IDs or closed enums, never arbitrary strings that become functions. Facts carry explicit units: longitude degrees in [0,360), angular separation degrees with circular semantics, ordinal house/sign values as distinct integer types, and timestamps as timezone-aware instants. Reject NaN, infinity, boolean-as-number, incompatible units and out-of-range ordinals. Conversion belongs to the calculation layer with a recorded convention, not model prose.

Pydantic strict validation reduces coercion; discriminated unions identify condition node variants explicitly [S3, S4]. Reject unknown fields recursively. JSON Schema permits additional properties by default, so closure must be deliberate [S5]. Declare the schema dialect and test both server and serialized-JSON boundaries; strict behavior can differ by input route. JSON Schema `format` annotation alone is not a guaranteed timestamp or identifier check [S6]. Structural validation cannot replace authorization, reference resolution, domain review or semantic support.

## Reviewed condition language

Represent conditions as data trees with allowlisted node kinds: `all`, `any`, `not`, typed equality, membership, bounded numeric comparison and registered fact references. A registered circular-distance comparison names its unit and boundary convention. No Python expressions, `eval`, dynamic imports, executable templates, arbitrary attribute traversal, URLs or user-defined functions are allowed.

Proposed initial limits are depth 8, 128 nodes, 32 referenced facts and 16 exception clauses per rule. Reject cycles, dangling references, empty conjunction/disjunction groups and unsupported operators before review. These are implementation limits to verify, not measured capacity. Free text remains annotation and never changes evaluation.

Use three explicit values: true, false and unknown. Missing, unstable, ineligible or unreviewed facts yield unknown with a reason code. `not unknown` stays unknown. `all` is false if any operand is false, true only if every operand is true, otherwise unknown. `any` is true if an operand is true, false only if every operand is false, otherwise unknown. Thus a known true alternative can establish a disjunction, but unknown itself never becomes true.

Applicability is condition AND NOT(any exception), subject to eligible scope, complete exception review and valid dependencies. An empty exception list is allowed only after reviewers explicitly attest that the reviewed source context requires none. Missing exception review prevents an applicable result. A true exception blocks application; an unknown exception prevents positive confirmation. A false primary condition remains not applicable even if another operand is unknown; retain the missing-input warning.

Unknown birth time never unlocks ascendant or houses in MVP. Approximate intervals require certified stability for each dependency across the permitted interval; matching endpoints alone are insufficient. Profile mismatch is `ineligible`, and withdrawn/unapproved revisions are `blocked`, separate from logical false. Errors cannot be turned into unknown and then treated as permission to generate a claim.

## Review, conflicts and explanation

Follow the editorial playbook's two-person executable-rule review. Approvals bind the source, predicate, exceptions and hash; editing any of them creates a new draft requiring fresh approvals. Rights approval and domain approval are separate. Activation also requires fixtures and resolved critical attribution defects. Withdrawal blocks new use immediately and follows the existing rights policy for stored readings.

A supersedes edge records a deliberate editorial replacement, not deletion or automatic invalidation of historical evaluations. Equivalence requires reviewed matching semantics, scope and exceptions; translation similarity is at most a discovery signal. Do not apply transitive equivalence automatically across schools. Conflicting rules remain separately attributable; no majority vote, confidence average or source-count bonus establishes truth.

Store an explainable reason ledger: evaluation ID; chart/settings hash; rule revision; each predicate's input fact IDs and truth state; exception results; missing prerequisites; approval references; permitted source locators; final status; and conflict IDs. This is a concise inspection record, not hidden chain-of-thought or a request for private model reasoning. Narrative generation consumes the ledger and cannot overwrite it.

## Fictional worked fixture

The following is entirely synthetic and describes no real astrology teaching, author or verse. Fixture passage P in invented edition E says condition A together with B suggests fictional quality Q, except when C holds. Its test-only rule revision R requires A AND B AND NOT C. Mock facts provide A=true, B=true and C=unknown because its fictional dependency is unavailable.

The ledger records primary condition true, exception unknown and applicability unknown. A textual explanation of what fixture P says is possible; a personalized assertion of Q is withheld. Changing C to false yields applicable only when scope, approvals and completeness checks pass. Changing C to true yields not applicable. The fixture belongs outside production corpus discovery.

## Acceptance cases

These are proposed tests; none has run.

| Case | Expected outcome |
|---|---|
| True conjunction, false reviewed exception | Applicable |
| True conjunction, unknown exception | Unknown; withhold personalized conclusion |
| False conjunct plus unknown conjunct | Not applicable; preserve missing-input reason |
| Negation of unknown | Unknown |
| Disjunction true plus unknown | True without converting unknown |
| Empty logical group | Schema rejection |
| Unknown-time house dependency | Ineligible prerequisite; no fabricated house |
| Interval crosses internal boundary | Unstable fact; unknown despite equal endpoints |
| Rashi value used as bhava | Type rejection |
| Degrees compared with ordinal | Unit/type rejection |
| Unsupported school or D9 chart | Ineligible scope |
| Unknown field or operator | Structural rejection |
| Nested tree exceeds limits | Bounded validation rejection |
| Executable text in annotation | Inert text; no execution |
| Edited approved predicate | New draft; old approvals insufficient |
| Withdrawn passage before publication | Block dependent claim |
| Commentary mislabeled original | Attribution review failure |
| Equivalent labels, different exceptions | No automatic equivalence |
| Conflicting reviewed conclusions | Separate attributed views and disagreement |
| Same revision and snapshot reevaluated | Same truth states and reason ledger |

## Primary sources and access record

All six sources returned HTTP 200 and readable relevant sections through direct retrieval on 2026-11-15. The web tool returned no readable payload; direct HTTP supplied inspection. Standards inform the design; no library compatibility or astrology source verification is claimed.

- S1 — W3C PROV-O: `https://www.w3.org/TR/prov-o/`. Entity, agent, activity, derivation and revision definitions inspected.
- S2 — W3C SKOS Reference: `https://www.w3.org/TR/skos-reference/`. Concept schemes, labels, semantic and mapping relations inspected.
- S3 — Pydantic strict mode: `https://docs.pydantic.dev/latest/concepts/strict_mode/`. Strict/lax behavior and input-route qualifications inspected; mutable documentation.
- S4 — Pydantic unions: `https://docs.pydantic.dev/latest/concepts/unions/`. Discriminated unions and smart-union compatibility warning inspected.
- S5 — JSON Schema object reference: `https://json-schema.org/understanding-json-schema/reference/object`. Additional-properties defaults and closure inspected.
- S6 — JSON Schema 2020-12 validation: `https://json-schema.org/draft/2020-12/json-schema-validation`. Format annotation/assertion distinction inspected.
