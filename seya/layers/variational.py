from keras import backend as K
from keras.layers.core import Layer
from keras import initializations, activations

from seya.regularizers import GaussianKL


class VariationalDense(Layer):
    def __init__(self, output_dim, batch_size, init='glorot_uniform', activation='linear',
                 weights=None, input_dim=None, **kwargs):
        self.batch_size = batch_size
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.output_dim = output_dim
        self.initial_weights = weights
        self.input_dim = input_dim
        if self.input_dim:
            kwargs['input_shape'] = (self.input_dim,)
        self.input = K.placeholder(ndim=2)
        super(VariationalDense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[1]

        self.W_mean = self.init((input_dim, self.output_dim))
        self.b_mean = K.zeros((self.output_dim,))
        self.W_logsigma = self.init((input_dim, self.output_dim))
        self.b_logsigma = K.zeros((self.output_dim,))

        self.params = [self.W_mean, self.b_mean, self.W_logsigma,
                       self.b_logsigma]

        self.regularizers = []
        mean, logsigma = self.get_mean_logsigma()
        self.regularizers.append(GaussianKL(mean, logsigma))

    def get_mean_logsigma(self, train=False):
        X = self.get_input(train)
        mean = self.activation(K.dot(X, self.W_mean) + self.b_mean)
        logsigma = self.activation(K.dot(X, self.W_logsigma) + self.b_logsigma)
        return mean, logsigma

    def get_output(self, train=False):
        mean, logsigma = self.get_mean_logsigma(train=train)
        if train:
            eps = K.random_normal((self.batch_size, self.output_dim))
            return mean + K.exp(logsigma) * eps
        else:
            return mean

    @property
    def output_shape(self):
        return (self.input_shape[0], self.output_dim)
