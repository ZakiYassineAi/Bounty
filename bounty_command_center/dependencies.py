from . import user_manager, target_manager, evidence_manager

def get_user_manager():
    """Dependency to get user manager."""
    return user_manager.UserManager()

def get_target_manager():
    """Dependency to get target manager."""
    return target_manager.TargetManager()

def get_evidence_manager():
    """Dependency to get evidence manager."""
    return evidence_manager.EvidenceManager()
