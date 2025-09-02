# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\schemas\bot.py
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid

class CoverageTestRequest(BaseModel):
    """Request schema for coverage test analysis"""
    project_id: uuid.UUID

class RequirementCoverage(BaseModel):
    """Schema for requirement coverage metrics"""
    total_requirements: int
    covered_requirements: int
    requirement_coverage_percent: float

class FeatureCoverage(BaseModel):
    """Schema for feature coverage metrics"""
    total_functional_requirements: int
    covered_functional_requirements: int
    functional_coverage_percent: float

class HighRiskCoverage(BaseModel):
    """Schema for high-risk coverage metrics"""
    total_high_risk_requirements: int
    covered_high_risk_requirements: int
    high_risk_coverage_percent: float

class RequirementMapping(BaseModel):
    """Schema for requirement to test case mapping"""
    requirement_id: str
    covered_by: List[str]

class CoverageAnalysisResult(BaseModel):
    """Complete coverage analysis result"""
    requirement_coverage: RequirementCoverage
    feature_coverage: FeatureCoverage
    high_risk_coverage: HighRiskCoverage
    requirement_to_testcase_mapping: List[RequirementMapping]

class CoverageTestResponse(BaseModel):
    """Response schema for coverage test analysis"""
    success: bool
    project_id: str
    coverage_analysis: CoverageAnalysisResult
