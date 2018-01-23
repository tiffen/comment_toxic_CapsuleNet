import mxnet as mx
from mxnet import init
from mxnet import nd
from mxnet.gluon import nn,rnn
from conv_cap import PrimeConvCap, AdvConvCap
from capsule_block import CapFullyBlock, LengthBlock
import config

def net():
    net = nn.Sequential()
    with net.name_scope():
        net.add(nn.Embedding(config.MAX_WORDS, config.EMBEDDING_DIM))
        net.add(rnn.GRU(128,layout='NTC',bidirectional=True, num_layers=2))#, dropout=0.2))
        net.add(transpose(axes=(0,2,1)))
        # net.add(nn.Conv2D(128, kernel_size=(101,1), padding=(50,0), groups=128,activation='relu'))
        net.add(PrimeConvCap(8,32, kernel_size=(1,1), padding=(0,0)))
        # net.add(AdvConvCap(8,32,8,32, kernel_size=(9,1), padding=(4,0)))
        net.add(CapFullyBlock(8*(config.MAX_LENGTH), num_cap=12, input_units=32, units=16, route_num=5))
        # net.add(CapFullyBlock(8*(config.MAX_LENGTH-8), num_cap=12, input_units=32, units=16, route_num=5))
        net.add(nn.Dropout(0.2))
        # net.add(LengthBlock())
        net.add(nn.Dense(6, activation='sigmoid'))
    net.initialize(init=init.Xavier())
    return net

class transpose(nn.Block):
    def __init__(self, axes, **kwargs):
        super(transpose, self).__init__(**kwargs)
        self.axes = axes

    def forward(self, x):
        return nd.transpose(x, axes=self.axes).reshape((0,0,0,1))

