from typing import List, Optional, Dict, Any, Union ,Literal
from pydantic import BaseModel, HttpUrl, Field, validator ,ConfigDict ,field_validator
from enum import Enum


# Enums for constrained choices
class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    CHART = "chart"
    DIAGRAM = "diagram"
    OTHER = "other"
    

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    STRONG ="strong"

class ImportanceLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ImplementationDifficulty(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    VERY_HARD = "very-hard"

class MediaItem(BaseModel):
    type: MediaType = Field(..., description="Type of media (image, diagram, etc.)")
    url: str = Field(..., description="Reference to the media (e.g., 'Figure 8', 'Table 2')")
    description: str = Field(..., description="Description of the media content")
    metadata:Optional[str] = Field(None, description="Additional metadata about the media")
    @field_validator('type', mode='before')
    def normalize_media_type(cls, v):
        if isinstance(v, str):
            # Map common variations
            mapping = {
                'image': 'image',
                'video': 'video',
                'chart': 'chart',
                'diagram': 'diagram',
                'other': 'other'
            }
            return mapping.get(v, 'other')
        return v

# Core Evidence Model
class Evidence(BaseModel):
    sources: List[HttpUrl] = Field(default_factory=list, description="Source URLs or DOIs")
    media: List[MediaItem] = Field(default_factory=list, description="Supporting media")
    links: List[HttpUrl] = Field(default_factory=list, description="Related web references")
    tables: List[str] = Field(default_factory=list, description="Table Captions or references")
    citations: List[Union[str, int]] = Field(default_factory=list, description="Page/chunk references or quotes")
    document_sections: List[str] = Field(default_factory=list, description="Source document sections")
    
    class Config:
        json_encoders = {
            HttpUrl: lambda v: str(v),
        }


class RelationType(str, Enum):
    CAUSES = "causes"
    MITIGATES = "mitigates"
    LEADS_TO = "leads-to"
    PART_OF = "part-of"
    RELATED_TO = "related-to"
    ENABLES = "enables"
    REQUIRES = "requires"
    TRIGGERS = "triggers"
    PREVENTS = "prevents"
    SUPPORTS = "supports"
    COORDINATES_WITH = "coordinates-with"
    REPORTS_TO = "reports-to"
    DEPENDS_ON = "depends-on"
    IMPLEMENTS = "implements"
    EVALUATES = "evaluates"
    MONITORS = "monitors"
    DETECTED_BY = "detected-by"
    CUSTOM ="custom"

class Relation(BaseModel):
    type: RelationType = Field(..., description="Type of relationship")
    target: str = Field(..., description="Target concept name")
    note: Optional[str] = Field(None, description="Specific nature of the relationship")
    strength: Optional[Literal["low", "medium", "high","strong"]] = Field(
        None, 
        description="Strength of the relationship (low|medium|high|strong)"
    )
    custom_type: Optional[str] = Field(
        None,
        description="Custom relation type name (only used when type is 'custom')"
    )
    conditions: Optional[str] = Field(None, description="Conditions under which this relationship applies")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")
    @field_validator('type', mode='before')
    def normalize_relation_type(cls, v):
        if isinstance(v, str):
            v = v.lower().replace('_', '-')
            # Map common variations
            mapping = {
                'causes': 'leads-to',
                'affects': 'leads-to',
                'outcome-of': 'leads-to',
                'part-of': 'part-of',
                'contains': 'part-of',
                'has-part': 'part-of'
            }
            return mapping.get(v, 'related-to')
        return v

class TargetType(str, Enum):
    CONCEPT = "Concept"
    SUBCONCEPT = "SubConcept"

class CrossReference(BaseModel):
    target: str = Field(..., description="Name of the target node")
    target_type: Optional[TargetType] = Field(None, description="Type of the target node")
    note: Optional[str] = Field(None, description="Description of the relationship")
    relationship_strength: Optional[ConfidenceLevel] = Field(None, description="Strength of the relationship")
    bidirectional: bool = Field(False, description="Whether the relationship is bidirectional")


# Extended Metadata Models
class ExtractionMetadata(BaseModel):
    extraction_focus: Optional[str] = Field(
        None, 
        description="Primary focus of extraction: operational, theoretical, or mixed"
    )
    completeness_score: Optional[int] = Field(
        None, 
        ge=1, 
        le=10, 
        description="Self-assessed completeness score (1-10)"
    )

class Metadata(BaseModel):
    doc_id: Optional[str] = Field(None, description="Document identifier")
    author: Optional[str] = Field(None, description="Author of the document")
    provenance: Optional[str] = Field(None, description="Source or origin of the content")
    original_name: Optional[str] = Field(None, description="Original name before normalization")
    importance: Optional[ImportanceLevel] = Field(None, description="Importance level of the content")
    confidence: Optional[ConfidenceLevel] = Field(None, description="Confidence in the extraction")
    extraction_metadata: Optional[ExtractionMetadata] = Field(None, description="Extraction-specific metadata")


class AssertionType(str, Enum):
    FACT = "fact"
    INSTRUCTION = "instruction"
    REQUIREMENT = "requirement"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    EXAMPLE = "example"

    
class Assertion(BaseModel):
    text: str = Field(..., description="The actual assertion text")
    assertion_type: AssertionType = Field(AssertionType.FACT, description="Type of assertion")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Confidence in the assertion")
    evidence: Evidence = Field(default_factory=Evidence, description="Supporting evidence")
    cross_references: List[CrossReference] = Field(
        default_factory=list, 
        description="References to other concepts"
    )
    extensions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Dynamic extras from LLM (e.g., emergent relations or untagged concepts)"
    )
    model_config = ConfigDict(extra='allow')
    @field_validator('assertion_type', mode='before')
    @classmethod
    def normalize_assertion_type(cls, v):
        if isinstance(v, str):
            v = v.lower().strip()
            mapping = {
                'definition': 'fact',
                'info': 'fact',
                'note': 'fact',
                'suggestion': 'recommendation',
                'tip': 'recommendation',
                'step': 'instruction',
                'direction': 'instruction',
                'howto': 'instruction',
                'warning': 'warning',
                'example': 'example',
                'requirement': 'requirement'
            }
            return mapping.get(v, 'fact')
        return v
    @validator('text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Assertion text cannot be empty')
        return v.strip()


# Operational Details Models
class OperationalDetails(BaseModel):
    practical_measures: List[str] = Field(default_factory=list, description="Actionable steps or procedures")
    implementation_steps: List[str] = Field(default_factory=list, description="How to execute/implement")
    resources_required: List[str] = Field(default_factory=list, description="Personnel, equipment, materials needed")
    timeline_indicators: List[str] = Field(default_factory=list, description="Duration, frequency, scheduling")
    success_criteria: List[str] = Field(default_factory=list, description="Measurable outcomes, KPIs")
    common_challenges: List[str] = Field(default_factory=list, description="Typical obstacles, pitfalls")
    best_practices: List[str] = Field(default_factory=list, description="Proven approaches, recommendations")

class ContextualExamples(BaseModel):
    real_world_cases: List[str] = Field(default_factory=list, description="Specific examples and case studies")
    hypothetical_scenarios: List[str] = Field(default_factory=list, description="What-if situations")
    quantitative_data: List[str] = Field(default_factory=list, description="Statistics, measurements, thresholds")
    qualitative_indicators: List[str] = Field(default_factory=list, description="Characteristics, symptoms, signs")

class StakeholderEcosystem(BaseModel):
    primary_actors: List[str] = Field(default_factory=list, description="Directly involved/responsible parties")
    supporting_actors: List[str] = Field(default_factory=list, description="Parties providing assistance/resources")
    coordination_mechanisms: List[str] = Field(default_factory=list, description="How different actors work together")
    communication_flows: List[str] = Field(default_factory=list, description="Information sharing patterns")
    decision_authorities: List[str] = Field(default_factory=list, description="Who makes what decisions")

class ExecutionDetails(BaseModel):
    how_to_perform: Optional[str] = Field(None, description="Step-by-step instructions")
    who_performs: Optional[str] = Field(None, description="Specific roles/actors responsible")
    when_performed: Optional[str] = Field(None, description="Timing, triggers, frequency")
    where_performed: Optional[str] = Field(None, description="Location, setting, environment")
    duration: Optional[str] = Field(None, description="Time required")
    prerequisites: Optional[list] = Field(None, description="What must be in place first")
    deliverables: Optional[list] = Field(None, description="Expected outputs/results")
    @field_validator("prerequisites", "deliverables", mode="before")
    def normalize_list(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return [v]  # wrap single string into list
        if isinstance(v, list):
            return v
        return [str(v)]

class PerformanceIndicators(BaseModel):
    success_metrics: List[str] = Field(default_factory=list, description="How to measure success")
    warning_signs: List[str] = Field(default_factory=list, description="Indicators of problems/failures")
    quality_standards: List[str] = Field(default_factory=list, description="Expected performance levels")
    compliance_requirements: List[str] = Field(default_factory=list, description="Regulatory/policy mandates")

class DomainSpecificPatterns(BaseModel):
    workflows: List[str] = Field(default_factory=list, description="End-to-end process flows")
    decision_trees: List[str] = Field(default_factory=list, description="Decision points and branching logic")
    escalation_paths: List[str] = Field(default_factory=list, description="How issues get elevated")
    feedback_loops: List[str] = Field(default_factory=list, description="Self-reinforcing or corrective cycles")
    integration_points: List[str] = Field(default_factory=list, description="Connections to other domains")

class ExtractionCompleteness(BaseModel):
    theoretical_coverage: Optional[str] = Field(None, description="Percentage estimate of theoretical concepts captured")
    operational_coverage: Optional[str] = Field(None, description="Percentage estimate of practical details captured")
    example_coverage: Optional[str] = Field(None, description="Percentage estimate of examples/cases captured")
    stakeholder_coverage: Optional[str] = Field(None, description="Percentage estimate of roles/actors captured")
    missing_elements: List[str] = Field(default_factory=list, description="What seems to be missing or underrepresented")

class SubConcept(BaseModel):
    name: str = Field(..., description="Name of the sub-concept")
    explanation: Optional[str] = Field(None, description="Detailed explanation including purpose and context")
    sub_type: Optional[str] = Field(
        None,
        description="Type of sub-concept (e.g., Phase, Step, Method, Procedure, etc.)"
    )
    
    # Core fields
    execution_details: Optional[ExecutionDetails] = Field(None, description="How to execute this sub-concept")
    performance_indicators: Optional[PerformanceIndicators] = Field(None, description="How to measure success")
    assertions: List[Assertion] = Field(default_factory=list, description="Factual claims or instructions")
    
    # Relationships
    cross_references: List[CrossReference] = Field(default_factory=list, description="References to other concepts")
    related_concepts: List[str] = Field(default_factory=list, description="Names of related concepts")
    relations: List[Relation] = Field(default_factory=list, description="Relationships to other concepts")
    
    # Metadata
    metadata: Optional[Metadata] = Field(None, description="Additional metadata")
    importance: Optional[ImportanceLevel] = Field(None, description="Importance level")
    implementation_difficulty: Optional[ImplementationDifficulty] = Field(None, description="Implementation complexity")
    
    # Backward compatibility
    sources: List[HttpUrl] = Field(default_factory=list, description="[Deprecated] Use evidence.sources instead")
    media: List[MediaItem] = Field(default_factory=list, description="[Deprecated] Use evidence.media instead")
    links: List[HttpUrl] = Field(default_factory=list, description="[Deprecated] Use evidence.links instead")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="[Deprecated] Use evidence.tables instead")
    
    class Config:
        json_encoders = {
            HttpUrl: lambda v: str(v),
        }


class Concept(BaseModel):
    name: str = Field(..., description="Name of the concept")
    concept_type: Optional[str] = Field(
        None,
        description="Type of concept (e.g., Definition, Framework, Process, etc.)"
    )
    
    # Core fields
    operational_details: Optional[OperationalDetails] = Field(None, description="Practical implementation details")
    contextual_examples: Optional[ContextualExamples] = Field(None, description="Real-world examples and scenarios")
    stakeholder_ecosystem: Optional[StakeholderEcosystem] = Field(None, description="Involved parties and their interactions")
    
    # Relationships
    related_concepts: List[str] = Field(default_factory=list, description="Names of related concepts")
    relations: List[Relation] = Field(default_factory=list, description="Relationships to other concepts")
    
    # Hierarchical structure
    sub_concepts: List[SubConcept] = Field(default_factory=list, description="Child concepts")
    
    # Metadata
    metadata: Optional[Metadata] = Field(None, description="Additional metadata")
    extensions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Dynamic extras from LLM (e.g., emergent relations or untagged concepts)"
    )
    
    model_config = ConfigDict(extra='allow')


class DocumentExtraction(BaseModel):
    domain: Optional[str] = Field(None, description="Specific domain or field")
    
    # Core content
    concepts: List[Concept] = Field(default_factory=list, description="Main concepts in the document")
    
    # Domain-specific patterns
    domain_specific_patterns: Optional[DomainSpecificPatterns] = Field(
        None, 
        description="Recurring patterns in the domain"
    )
    
    # Extraction metadata
    extraction_completeness: Optional[ExtractionCompleteness] = Field(
        None, 
        description="Self-assessment of extraction quality"
    )
    
    # General metadata
    metadata: Optional[Metadata] = Field(None, description="Document-level metadata")
    
    # class Config:
    #     json_encoders = {
    #         HttpUrl: lambda v: str(v),
    #     }
    model_config = ConfigDict(extra='allow')

class DynamicRelation(BaseModel):
    type: str  # e.g., "causes" or custom
    target: str
    note: Optional[str] = None
    emergent: bool = True  # Flag for LLM-generated extras
class ExtractionBatchRecord(BaseModel):
    doc_id: str = Field(..., description="Document identifier")
    payload: DocumentExtraction = Field(..., description="Extracted document content")
    batch_index: Optional[int] = Field(None, description="Index of current batch (0-based)")
    total_batches: Optional[int] = Field(None, description="Total number of batches for this document")
    
    @validator('batch_index')
    def validate_batch_index(cls, v, values):
        if v is not None and 'total_batches' in values and values['total_batches'] is not None:
            if v < 0:
                raise ValueError('batch_index cannot be negative')
            if v >= values['total_batches']:
                raise ValueError('batch_index must be less than total_batches')
        return v
