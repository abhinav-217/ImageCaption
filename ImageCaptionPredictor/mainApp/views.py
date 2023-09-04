from django.shortcuts import render,HttpResponse
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
import cv2
from keras.models import load_model
from keras.utils import to_categorical
import numpy as np
from keras.applications import ResNet50
from keras.optimizers import Adam
from keras.layers import Dense, Flatten, Input, Convolution2D, Dropout, LSTM, TimeDistributed, Embedding, Bidirectional, Activation, RepeatVector, Concatenate
from keras.models import Sequential, Model
from keras.preprocessing import image, sequence
from keras.preprocessing.sequence import pad_sequences
from tqdm import tqdm
import os
# Create your views here.

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainApp'
    

vocab_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vocab.npy')
vocab = np.load(vocab_file_path, allow_pickle=True)
vocab = vocab.item() 
inv_vocab = {v: k for k, v in vocab.items()}


# Define constants
embedding_size = 128
vocab_size = len(vocab)
max_len = 40

# Define the image model
image_model = Sequential()
image_model.add(Dense(embedding_size, input_shape=(2048,), activation='relu'))
image_model.add(RepeatVector(max_len))

language_model = Sequential()
language_model.add(Embedding(input_dim=vocab_size, output_dim=embedding_size, input_length=max_len))
language_model.add(LSTM(256, return_sequences=True))
language_model.add(TimeDistributed(Dense(embedding_size)))

conca = Concatenate()([image_model.output, language_model.output])
x = LSTM(128, return_sequences=True)(conca)
x = LSTM(512, return_sequences=False)(x)
x = Dense(vocab_size)(x)
out = Activation('softmax')(x)
model = Model(inputs=[image_model.input, language_model.input], outputs=out)
model.compile(loss='categorical_crossentropy', optimizer='RMSprop', metrics=['accuracy'])
mine_model_weight_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mine_model_weights.h5')
model.load_weights(mine_model_weight_path)

resnet = ResNet50(include_top=False, weights='imagenet', input_shape=(224, 224, 3), pooling='avg')

def index(request):
    return render(request,'index.html')

def generate(request):
    if request.method == 'POST' and 'file1' in request.FILES:
        img = request.FILES['file1']
        fs = FileSystemStorage()
        filename = fs.save('static/file.jpg', img)
        image = cv2.imread(filename)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (224, 224))
        image = np.reshape(image, (1, 224, 224, 3))
        incept = resnet.predict(image).reshape(1, 2048)
        text_in = ['startofseq']
        final = ''
        count = 0
        while count < 20:
            count += 1
            encoded = []
            for i in text_in:
                encoded.append(vocab[i])

            padded = pad_sequences([encoded], maxlen=max_len, padding='post', truncating='post').reshape(1, max_len)
            sampled_index = np.argmax(model.predict([incept, padded]))
            sampled_word = inv_vocab[sampled_index]

            if sampled_word != 'endofseq':
                final = final + ' ' + sampled_word
            text_in.append(sampled_word)
            print(final)
        # print("the reuestis :",request.FILES)
        return render(request,'generate.html',{'file':filename,'result':final})