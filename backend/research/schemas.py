"""Public plans and evidence-linked reports; no hidden reasoning transcripts."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.debate.schemas import Claim

Dimension = Literal['personal', 'playoffs', 'honors', 'teammates', 'opponents', 'era', 'game']
DIMENSIONS = ('personal', 'playoffs', 'honors', 'teammates', 'opponents', 'era')


class Task(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dimension: Dimension
    question: str = Field(min_length=8, max_length=1800)
    gap_id: str = Field(default='',max_length=80,description='For a targeted content follow-up, copy an actionable gap ID from the Lead evidence review. Empty for initial collection or collection recovery.')


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['clarify', 'lookup', 'research', 'finish']
    question: str = Field(default='', max_length=4000)
    scope: str = Field(default='', max_length=1600)
    criteria: str = Field(default='', max_length=1600)
    comprehensive: bool = False
    tasks: list[Task] = Field(default_factory=list, max_length=6)

    @model_validator(mode='after')
    def valid_action(self):
        if self.action == 'clarify' and not self.question.strip():
            raise ValueError('Clarification requires a question for the user.')
        if self.action == 'research' and not self.tasks:
            raise ValueError('Research requires tasks.')
        if self.action == 'research' and (not self.scope.strip() or not self.criteria.strip()):
            raise ValueError('Research requires an explicit scope and comparison/research criteria.')
        if self.action != 'research' and self.tasks:
            raise ValueError('Only research may contain tasks.')
        return self


class FactPointer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    evidence_id: str
    metric: str
    player_id: int | None = None


class Section(BaseModel):
    model_config = ConfigDict(extra='forbid')
    heading: str = Field(max_length=160)
    text: str = Field(min_length=1,max_length=5000)
    evidence_ids: list[str] = Field(default_factory=list,max_length=12)


class Report(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: str = Field(default='', max_length=24000)
    sections: list[Section] = Field(default_factory=list,max_length=10)
    facts: list[FactPointer] = Field(default_factory=list,max_length=24)
    claims: list[Claim] = Field(default_factory=list, max_length=64)

    @model_validator(mode='after')
    def content(self):
        if not self.answer.strip() and not self.sections:
            raise ValueError('Provide report sections or an answer.')
        return self


class Review(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sections: list[Section] = Field(min_length=1,max_length=10)
    corrections: list[str] = Field(default_factory=list,max_length=12)
