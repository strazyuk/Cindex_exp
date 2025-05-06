
# def numEquivDominoPairs(dominoes):
#     num = [0] * 100
#     ret = 0
#     for x, y in dominoes:
#         print(x,y)
#         val = x * 10 + y if x <= y else y * 10 + x
#         print(val)
#         ret += num[val]
#         print(ret)          
#         num[val] += 1
#     return ret
# x=numEquivDominoPairs([[1,2],[2,1],[2,3],[3,4],[4,3],[5,6],[7,8]])
# print(x)
import numpy as np
import matplotlib.pyplot as plt

class KohonenSOM:
    def __init__(self, input_dim, grid_size, learning_rate=0.1, radius=None, decay_rate=0.01):
        self.input_dim = input_dim
        self.grid_size = grid_size  # (rows, cols)
        self.learning_rate = learning_rate
        self.initial_lr = learning_rate
        self.radius = radius if radius else max(grid_size) / 2
        self.initial_radius = self.radius
        self.decay_rate = decay_rate
        self.weights = np.random.rand(grid_size[0], grid_size[1], input_dim)
        self.grid = np.array([[np.array([i, j]) for j in range(grid_size[1])] for i in range(grid_size[0])])

    def train(self, data, num_epochs=1000):
        for epoch in range(num_epochs):
            sample = data[np.random.randint(0, len(data))]
            winner = self.find_bmu(sample)
            self.update_weights(sample, winner, epoch, num_epochs)

    def find_bmu(self, sample):
        distances = np.linalg.norm(self.weights - sample, axis=2)
        return np.unravel_index(np.argmin(distances), self.weights.shape[:2])

    def update_weights(self, sample, winner, epoch, num_epochs):
        lr = self.initial_lr * np.exp(-epoch / num_epochs)
        radius = self.initial_radius * np.exp(-epoch / num_epochs)
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                neuron_pos = np.array([i, j])
                dist = np.linalg.norm(neuron_pos - winner)
                if dist <= radius:
                    influence = np.exp(-(dist**2) / (2 * (radius**2)))
                    self.weights[i, j] += influence * lr * (sample - self.weights[i, j])

    def map_input(self, sample):
        return self.find_bmu(sample)

    def visualize(self, data):
        plt.figure(figsize=(8, 6))
        for sample in data:
            bmu = self.map_input(sample)
            plt.plot(bmu[1], bmu[0], 'ro')
        plt.title("Self-Organizing Map Projection")
        plt.gca().invert_yaxis()
        plt.show()

# Example usage
if __name__ == "__main__":
    # Generate some random 3D data
    data = np.random.rand(500, 3)
    som = KohonenSOM(input_dim=3, grid_size=(10, 10))
    som.train(data, num_epochs=1000)
    som.visualize(data)
