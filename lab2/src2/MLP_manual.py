import numpy as np
from matplotlib import pyplot as plt
import torch

LOSS_STEP = 4
COMPARE_TO_TORCH = False
PRINT_NET = True


class NNLayer:
    def forward(self, x):
        raise NotImplementedError

    def backward(self, grad_y):
        raise NotImplementedError

    def train(self):
        raise NotImplementedError

    def eval(self):
        raise NotImplementedError


class LinearLayer(NNLayer):
    """
    Linear layer of MLP network
    """

    def __init__(self, input_size, output_size):
        self.input_size = input_size
        self.output_size = output_size
        self.last_input = None
        self.weights = np.random.randn(input_size, output_size) * np.sqrt(2 / input_size)
        self.bias = np.zeros((1, self.output_size))
        self.training = False

    def forward(self, x):
        if self.training:
            self.last_input = x
        return np.dot(x, self.weights) + self.bias

    def backward(self, grad_y):
        if self.last_input is None:
            raise RuntimeError("No input to back-propagate through")
        grad_bias = np.sum(grad_y, axis=0, keepdims=True)
        grad_weights = np.matmul(self.last_input.T, grad_y)
        grad_x = np.matmul(grad_y, self.weights.T)
        return grad_x, self.weights, grad_weights, self.bias, grad_bias

    def train(self):
        self.training = True

    def eval(self):
        self.training = False


class Tanh(NNLayer):
    """
    Thah layer of MLP network
    """

    def __init__(self):
        self.last_input = None
        self.is_training = False

    def forward(self, x):
        if self.is_training:
            self.last_input = x
        return np.tanh(x)

    def backward(self, grad_y):
        return (1 - np.power(np.tanh(self.last_input), 2)) * grad_y, None, None, None, None

    def train(self):
        self.is_training = True

    def eval(self):
        self.is_training = False


class SoftmaxCrossEntropy:
    """
    Softmax cross entropy loss layer of MLP network
    """

    def __init__(self):
        pass

    def __call__(self, scores, labels):
        scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
        scores /= np.sum(scores, axis=1, keepdims=True)
        positive_scores = scores[np.arange(batch_size), labels]
        loss = np.mean(-np.log(positive_scores))

        one_hot = np.zeros_like(scores)
        one_hot[np.arange(batch_size), labels] = 1.0
        grad = (scores - one_hot) / batch_size
        return loss, grad


class MLP:
    def __init__(self):
        # layer size = [10, 8, 8, 4]
        # ?????????????????????   
        self.layer_size = [10, 10, 8, 8, 4]
        self.layers = []
        self.loss = SoftmaxCrossEntropy()
        for i in range(len(self.layer_size) - 1):
            self.layers.append(LinearLayer(self.layer_size[i], self.layer_size[i + 1]))
            if i < len(self.layer_size) - 2:
                self.layers.append(Tanh())

    def forward(self, x):
        # ????????????
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, input, label, lr):  # ?????????????????????
        # ????????????
        weights_list = []
        grad_weights_list = []
        bias_list = []
        grad_bias_list = []
        pred = self.forward(input)
        loss, grad = self.loss(pred, label)
        for l in reversed(self.layers):
            grad, weights, grad_weights, bias, grad_bias = l.backward(grad)
            if weights is not None:
                weights_list.append(weights)
                grad_weights_list.append(grad_weights)
                bias_list.append(bias)
                grad_bias_list.append(grad_bias)
        for w, gw, b, gb in zip(weights_list, grad_weights_list, bias_list, grad_bias_list):
            w -= gw * lr
            b -= gb * lr
        return loss

    def train(self):
        for i in range(len(self.layers)):
            self.layers[i].train()

    def eval(self):
        for i in range(len(self.layers)):
            self.layers[i].eval()


def train(mlp: MLP, epochs, lr, inputs, input_labels, batch_size=10):
    """
        mlp: ??????????????????MLP??????
        epochs: ????????????
        lr: ?????????
        inputs: ?????????????????????
        labels: ?????????one-hot??????
    """
    mlp.train()
    global_step = 0
    num_input = inputs.shape[0]
    input_labels = np.argmax(input_labels, axis=1)
    loss_list = []
    accum_loss = 0.0
    for epoch in range(epochs):
        start_idx = 0
        shuffle_idx = np.random.permutation(num_input)
        while start_idx < num_input:
            end_idx = min(start_idx + batch_size, num_input)
            batch_idx = shuffle_idx[start_idx:end_idx]
            batch_input = inputs[batch_idx]
            batch_label = input_labels[batch_idx]
            loss = mlp.backward(batch_input, batch_label, lr)
            global_step += 1
            accum_loss += loss
            start_idx += batch_size
            if global_step % LOSS_STEP == 0:
                loss_list.append(accum_loss / LOSS_STEP)
                accum_loss = 0.0
                print(f"[Manual]Global step: {global_step}, epoch: {epoch}, loss: {loss}")
    if PRINT_NET:
        for i in range(len(mlp.layers)):
            if i % 2 == 0:
                print(f"Layer {int(i / 2)} weights:")
                print(mlp.layers[i].weights)
                print(f"Layer {int(i / 2)} bias:")
                print(mlp.layers[i].bias)
    return loss_list


def train_torch_mlp(epochs, lr, inputs, input_labels, batch_size):
    class TorchMLP(torch.nn.Module):
        def __init__(self):
            super(TorchMLP, self).__init__()
            self.mlp = torch.nn.Sequential(
                torch.nn.Linear(10, 10),
                torch.nn.Tanh(),
                torch.nn.Linear(10, 8),
                torch.nn.Tanh(),
                torch.nn.Linear(8, 8),
                torch.nn.Tanh(),
                torch.nn.Linear(8, 4)
            )
            self.loss = torch.nn.CrossEntropyLoss()

        def forward(self, x):
            return self.mlp(x)

    net = TorchMLP()
    net.train()
    optim = torch.optim.SGD(net.parameters(), lr=lr)
    global_step = 0
    num_input = inputs.shape[0]
    input_labels = np.argmax(input_labels, axis=1)
    loss_list = []
    accum_loss = 0.0
    for epoch in range(epochs):
        start_idx = 0
        shuffle_idx = np.random.permutation(num_input)
        while start_idx < num_input:
            end_idx = min(start_idx + batch_size, num_input)
            batch_idx = shuffle_idx[start_idx:end_idx]
            batch_input = torch.tensor(inputs[batch_idx], dtype=torch.float32)
            batch_label = torch.tensor(input_labels[batch_idx], dtype=torch.long)
            pred = net(batch_input)
            loss = net.loss(pred, batch_label)
            global_step += 1
            accum_loss += loss.item()
            optim.zero_grad()
            loss.backward()
            optim.step()
            start_idx += batch_size
            if global_step % LOSS_STEP == 0:
                loss_list.append(accum_loss / LOSS_STEP)
                accum_loss = 0.0
                print(f"[Torch]Global step: {global_step}, epoch: {epoch}, loss: {loss}")
    return loss_list


if __name__ == '__main__':
    # ??????????????????,???????????????????????????
    np.random.seed(1)
    mlp = MLP()
    # ????????????
    inputs = np.random.randn(100, 10)

    # ??????one-hot??????
    labels = np.eye(4)[np.random.randint(0, 4, size=(1, 100))].reshape(100, 4)

    # ??????
    epochs = 1100
    lr = 1e-2
    batch_size = 10
    manual_loss_list = train(mlp, epochs, lr, inputs, labels.astype(int), batch_size)

    if COMPARE_TO_TORCH:
        torch_loss_list = train_torch_mlp(epochs, lr, inputs, labels.astype(int), batch_size)
        plt.ylim(-0.1, 2.0)
        plt.plot(manual_loss_list, label='Manual MLP')
        plt.plot(torch_loss_list, label='Torch MLP')
        plt.legend()
        plt.show()
