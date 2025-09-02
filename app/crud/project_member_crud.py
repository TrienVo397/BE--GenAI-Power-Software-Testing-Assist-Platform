# filepath: app/crud/project_member_crud.py
"""
CRUD operations for project membership management
"""
from typing import List, Optional
from sqlmodel import Session, select
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.models.project import Project
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate
import uuid
import logging

logger = logging.getLogger(__name__)

class CRUDProjectMember:
    """CRUD operations for project members"""
    
    def add_member(
        self, 
        db: Session, 
        project_id: uuid.UUID, 
        member_data: ProjectMemberCreate,
        added_by: uuid.UUID
    ) -> ProjectMember:
        """Add a user to a project with a specific role"""
        
        # Check if membership already exists
        existing = self.get_membership(db, project_id, member_data.user_id)
        if existing:
            # Update existing membership instead of creating duplicate
            update_data = ProjectMemberUpdate(
                role=member_data.role,
                is_active=member_data.is_active
            )
            return self.update_membership(db, project_id, member_data.user_id, update_data, added_by)
        
        # Create new membership
        db_member = ProjectMember(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
            is_active=member_data.is_active,
            added_by=added_by,
            updated_by=added_by
        )
        
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        
        logger.info(f"Added user {member_data.user_id} to project {project_id} with role {member_data.role}")
        return db_member
    
    def get_membership(
        self, 
        db: Session, 
        project_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Optional[ProjectMember]:
        """Get a specific user's membership in a project"""
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
        return db.exec(statement).first()
    
    def get_project_members(
        self, 
        db: Session, 
        project_id: uuid.UUID,
        active_only: bool = True
    ) -> List[ProjectMember]:
        """Get all members of a project"""
        statement = select(ProjectMember).where(ProjectMember.project_id == project_id)
        if active_only:
            statement = statement.where(ProjectMember.is_active == True)
        return list(db.exec(statement).all())
    
    def get_user_memberships(
        self, 
        db: Session, 
        user_id: uuid.UUID,
        active_only: bool = True
    ) -> List[ProjectMember]:
        """Get all project memberships for a user"""
        statement = select(ProjectMember).where(ProjectMember.user_id == user_id)
        if active_only:
            statement = statement.where(ProjectMember.is_active == True)
        return list(db.exec(statement).all())
    
    def update_membership(
        self,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        update_data: ProjectMemberUpdate,
        updated_by: uuid.UUID
    ) -> Optional[ProjectMember]:
        """Update a user's membership in a project"""
        membership = self.get_membership(db, project_id, user_id)
        if not membership:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(membership, field, value)
        
        membership.updated_by = updated_by
        from datetime import datetime, timezone
        membership.updated_at = datetime.now(timezone.utc)
        
        db.add(membership)
        db.commit()
        db.refresh(membership)
        
        logger.info(f"Updated membership for user {user_id} in project {project_id}")
        return membership
    
    def remove_member(
        self,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Remove a user from a project (hard delete)"""
        membership = self.get_membership(db, project_id, user_id)
        if not membership:
            return False
        
        db.delete(membership)
        db.commit()
        
        logger.info(f"Removed user {user_id} from project {project_id}")
        return True
    
    def deactivate_member(
        self,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        updated_by: uuid.UUID
    ) -> Optional[ProjectMember]:
        """Deactivate a user's membership (soft delete)"""
        update_data = ProjectMemberUpdate(is_active=False)
        return self.update_membership(db, project_id, user_id, update_data, updated_by)
    
    def get_members_by_role(
        self,
        db: Session,
        project_id: uuid.UUID,
        role: ProjectRole,
        active_only: bool = True
    ) -> List[ProjectMember]:
        """Get all members of a project with a specific role"""
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.role == role
        )
        if active_only:
            statement = statement.where(ProjectMember.is_active == True)
        return list(db.exec(statement).all())
    
    def get_project_owners(self, db: Session, project_id: uuid.UUID) -> List[ProjectMember]:
        """Get all owners of a project"""
        return self.get_members_by_role(db, project_id, ProjectRole.OWNER)
    
    def get_project_managers(self, db: Session, project_id: uuid.UUID) -> List[ProjectMember]:
        """Get all users who can manage the project (owners, leads, managers)"""
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.role.in_([ProjectRole.OWNER, ProjectRole.LEAD, ProjectRole.MANAGER]),
            ProjectMember.is_active == True
        )
        return list(db.exec(statement).all())
    
    def user_can_manage_project(
        self,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Check if a user can manage a project"""
        membership = self.get_membership(db, project_id, user_id)
        if not membership or not membership.is_active:
            return False
        return membership.can_manage_project()
    
    def user_can_manage_members(
        self,
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Check if a user can manage project members"""
        membership = self.get_membership(db, project_id, user_id)
        if not membership or not membership.is_active:
            return False
        return membership.can_manage_members()
    
    def add_multiple_members(
        self,
        db: Session,
        project_id: uuid.UUID,
        members_data: List[ProjectMemberCreate],
        added_by: uuid.UUID
    ) -> List[ProjectMember]:
        """Add multiple users to a project at once"""
        added_members = []
        for member_data in members_data:
            try:
                member = self.add_member(db, project_id, member_data, added_by)
                added_members.append(member)
            except Exception as e:
                logger.error(f"Failed to add user {member_data.user_id} to project {project_id}: {e}")
                continue
        
        logger.info(f"Added {len(added_members)} members to project {project_id}")
        return added_members

# Create a singleton instance
project_member_crud = CRUDProjectMember()
