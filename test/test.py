import torch

# assert if torch tensor is available
assert torch.tensor([1,2,3]).shape == torch.Size([3])

assert torch.cuda.is_available() == True