from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models import BaseModel


class CommandBatch(BaseModel):
    __tablename__ = 'command_batches'
    __use_id_pk__ = False
    
    batch_id = Column(String(255), primary_key=True)  # Natural primary key
    command_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    note = Column(String(500), nullable=True)
    stats = Column(JSON, nullable=True)  # Store counts: {pending, sent, success, fail, etc.}
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship('User', back_populates='created_batches')
    commands = relationship('RemoteCommand', back_populates='batch', lazy='dynamic')
    
    def __repr__(self):
        return f'<CommandBatch {self.batch_id} {self.command_type}>'
    
    def update_stats(self):
        """Update statistics from related commands."""
        from app.models.remote_command import CommandStatus
        
        stats = {
            'total': 0,
            'pending': 0,
            'queued': 0,
            'sent': 0,
            'success': 0,
            'fail': 0,
            'unsupported': 0
        }
        
        for command in self.commands:
            stats['total'] += 1
            if command.status in stats:
                stats[command.status] += 1
        
        self.stats = stats
        return stats