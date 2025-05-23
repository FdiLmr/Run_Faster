"""Neural network models for marathon time prediction."""

import torch
from torch import nn
from typing import Tuple


class Neuromodel1(nn.Module):
    """Neural network model for marathon prediction using single race data.
    
    Input features:
    - Distance of race (meters)
    - Time of race (seconds)
    - Weekly training mileage (miles)
    
    Output:
    - Predicted marathon time (minutes)
    """
    
    def __init__(self, input_size: int = 3, hidden_sizes: Tuple[int, ...] = (7, 12)):
        super(Neuromodel1, self).__init__()
        
        if input_size != 3:
            raise ValueError("Neuromodel1 expects exactly 3 input features")
            
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU()
            ])
            prev_size = hidden_size
            
        # Output layer
        layers.append(nn.Linear(prev_size, 1))
        
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, 3)
            
        Returns:
            Predicted marathon time tensor of shape (batch_size, 1)
        """
        if x.shape[-1] != 3:
            raise ValueError(f"Expected input with 3 features, got {x.shape[-1]}")
        return self.network(x)


class Neuromodel2(nn.Module):
    """Neural network model for marathon prediction using two race data points.
    
    Input features:
    - Distance of race 1 (meters)
    - Time of race 1 (seconds)
    - Distance of race 2 (meters)
    - Time of race 2 (seconds)
    - Weekly training mileage (miles)
    
    Output:
    - Predicted marathon time (minutes)
    """
    
    def __init__(self, input_size: int = 5, hidden_sizes: Tuple[int, ...] = (5, 12)):
        super(Neuromodel2, self).__init__()
        
        if input_size != 5:
            raise ValueError("Neuromodel2 expects exactly 5 input features")
            
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU()
            ])
            prev_size = hidden_size
            
        # Output layer
        layers.append(nn.Linear(prev_size, 1))
        
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, 5)
            
        Returns:
            Predicted marathon time tensor of shape (batch_size, 1)
        """
        if x.shape[-1] != 5:
            raise ValueError(f"Expected input with 5 features, got {x.shape[-1]}")
        return self.network(x)