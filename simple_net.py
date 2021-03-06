import tensorflow as tf
import os
import numpy as np
import cv2
import json
import random
import shutil

# ref: https://github.com/MuhammedBuyukkinaci/TensorFlow-Binary-Image-Classification-using-CNN-s/blob/master/Binary_classification.ipynb
# tensorflow version 1.5

# dataset can be downloaded from http://mrl.cs.vsb.cz/eyedataset
def preprocess(directory_path="data/mrlEyes_2018_01"):
    dir_list = os.listdir(directory_path)
    image_dictionary = {}
    for dir in dir_list:
        dir = os.path.join(directory_path, dir)
        image_list = os.listdir(dir)
        for image in image_list:
            info = image.split("_")
            if int(info[3]) == 1: continue  # if wearing glasses
            if int(info[5]) == 2: continue  # if high reflection
            if int(info[6]) == 0: continue  # if lighting condition in bad
            if random.random() > 0.4: continue  # 20% sampling
            image_dictionary[os.path.join(dir, image)] = int(info[4])

    print(image_dictionary)
    resized_image_dictionary = {}
    shutil.rmtree('data/pupil_data')
    os.mkdir('data/pupil_data')

    image_label_list = []

    for image in image_dictionary.keys():
        open_closed = image_dictionary[image]
        img = cv2.imread(image, 0)
        if img is None: continue
        if img.shape[0] < 50 or img.shape[1] < 50: continue  # discard too small images
        img = cv2.resize(img, (50, 50), interpolation=cv2.INTER_AREA)
        _, dir, dir2, _ = image.split("/")
        image = image.replace(dir + '/' + dir2, "pupil_data")
        cv2.imwrite(image, img)
        resized_image_dictionary[image] = open_closed
        image_label_list.append([img, open_closed])

    with open('data/pupil_data_list.json', 'w') as f:
        json.dump(resized_image_dictionary, f)

    random.shuffle(image_label_list)
    train_image_list = image_label_list[:6000]
    test_image_list = image_label_list[6000:8000]

    train_images = np.array([x[0] for x in train_image_list])
    train_images = train_images / 255
    train_images = train_images.reshape((-1, 50, 50, 1))
    train_labels = np.array([[float(x[1])] for x in train_image_list])

    with open('data/train_image.npy', 'wb') as f:
        np.save(f, train_images)
    with open('data/train_label.npy', 'wb') as f:
        np.save(f, train_labels)

    test_images = np.array([x[0] for x in test_image_list])
    test_images = test_images / 255
    test_images = test_images.reshape((-1, 50, 50, 1))
    test_labels = np.array([[float(x[1])] for x in test_image_list])

    with open('data/test_image.npy', 'wb') as f:
        np.save(f, test_images)
    with open('data/test_label.npy', 'wb') as f:
        np.save(f, test_labels)


preprocess()


def simple_model(X, training=False):
    nodes_fc1 = 512
    # CONVOLUTION LAYER 1
    # Weights for layer 1
    w_1 = tf.Variable(tf.truncated_normal([11, 11, 1, 48], stddev=0.01))
    # Bias for layer 1
    b_1 = tf.Variable(tf.constant(0.0, shape=[[11, 11, 1, 48][3]]))
    # Applying convolution
    c_1 = tf.nn.conv2d(X, w_1, strides=[1, 1, 1, 1], padding='VALID')
    # Adding bias
    c_1 = c_1 + b_1
    # Applying RELU
    c_1 = tf.nn.relu(c_1)

    # POOLING LAYER1
    p_1 = tf.nn.max_pool(c_1, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='VALID')

    # CONVOLUTION LAYER 2
    # Weights for layer 2
    w_2 = tf.Variable(tf.truncated_normal([5, 5, 48, 96], stddev=0.01))
    # Bias for layer 2
    b_2 = tf.Variable(tf.constant(1.0, shape=[[5, 5, 48, 96][3]]))
    # Applying convolution
    c_2 = tf.nn.conv2d(p_1, w_2, strides=[1, 1, 1, 1], padding='SAME')
    # Adding bias
    c_2 = c_2 + b_2
    # Applying RELU
    c_2 = tf.nn.relu(c_2)

    # POOLING LAYER2
    p_2 = tf.nn.max_pool(c_2, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='VALID')

    # Flattening
    flattened = tf.reshape(p_2,[-1,9*9*96])

    # Fully Connected Layer 1
    # Getting input nodes in FC layer 1
    input_size = int(flattened.get_shape()[1])
    # Weights for FC Layer 1
    w1_fc = tf.Variable(tf.truncated_normal([input_size, nodes_fc1], stddev=0.01))
    # Bias for FC Layer 1
    b1_fc = tf.Variable(tf.constant(1.0, shape=[nodes_fc1]))
    # Summing Matrix calculations and bias
    s_fc1 = tf.matmul(flattened, w1_fc) + b1_fc
    # Applying RELU
    s_fc1 = tf.nn.relu(s_fc1)

    # Dropout Layer is not supported for vitis-ai

    # Fully Connected Layer 3
    # Weights for FC Layer 3
    w3_fc = tf.Variable(tf.truncated_normal([nodes_fc1, 1], stddev=0.01))
    # Bias for FC Layer 3b3_fc = tf.Variable( tf.constant(1.0, shape=[output_classes] ) )
    b3_fc = tf.Variable(tf.constant(1.0, shape=[1]))
    y_pred = tf.matmul(s_fc1, w3_fc) + b3_fc

    if training: return y_pred
    y_pred = tf.nn.relu(y_pred, name="final_output")
    return y_pred


# train the model
train_images = np.load('data/train_image.npy')
train_labels = np.load('data/train_label.npy')
train_size = len(train_images)
batch_x, batch_y = None, None
learning_rate = 1e-3
batch_size = 8
epoch = 30
save_point = 30
checkpoint_dir_path = 'data/'
with tf.device('/device:XLA_GPU:0'):
    with tf.Graph().as_default():
        X = tf.placeholder(tf.float32, shape=[None, 50, 50, 1], name="normalized_gray_image")
        y_true = tf.placeholder(tf.float32, shape=[None, 1], name="output")
        y_pred = simple_model(X, True)
        # loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(labels=y_true, logits=y_pred))
        loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(labels=y_true, logits=y_pred))
        global_step = tf.contrib.framework.get_or_create_global_step()
        train_op = tf.train.AdamOptimizer(learning_rate).minimize(loss, global_step=global_step)
        init = tf.global_variables_initializer()
        saver = tf.train.Saver()
        with tf.Session(config=tf.ConfigProto(log_device_placement=True)) as sess:
            sess.run(init)
            cur_loss = 0
            for i in range(1, epoch + 1):
                batch_epoch_size = int(len(train_images) / batch_size)
                for b_num in range(batch_epoch_size):
                    offset = b_num * batch_size
                    if offset + batch_size < train_size:
                        batch_x, batch_y = train_images[offset:(offset + batch_size)], train_labels[
                                                                             offset:(offset + batch_size)]
                    else:
                        batch_x, batch_y = train_images[offset:], train_labels[offset:]
                    _, cur_loss = sess.run([train_op, loss],
                                                    feed_dict={X: batch_x, y_true: batch_y})
                print("testing loss : ", i, cur_loss)

                if i % save_point == 0 or i == epoch:
                    saver.save(sess, os.path.join(checkpoint_dir_path, "model"), i)


# test the model
test_images = np.load('data/test_image.npy')
test_labels = np.load('data/test_label.npy')
checkpoint_path = 'data/model-30'

true= 0
X = tf.placeholder(tf.float32, [None, 50, 50, 1], name="normalized_gray_image")
output_0 = simple_model(X)
init = tf.global_variables_initializer()
saver = tf.train.Saver()
with tf.Session(config=tf.ConfigProto(log_device_placement=True)) as sess:
    sess.run(init)
    saver.restore(sess, checkpoint_path)
    for image, label in zip(test_images, test_labels):
        prediction = sess.run(output_0, feed_dict={X: [image]})
        print("prediction : ", prediction)
        print("ground_truth : ", label)
        pred = round(prediction[0][0])
        pred = 0 if pred == 0 else 1
        if pred == round(label[0]): true += 1
        else:
            cv2.imshow("test", image)
            cv2.waitKey(30)
        image = image
        message = "c" if round(prediction[0][0]) == 0 else "o"
        cv2.putText(image, message, (0, 40), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)
        message = "c" if label[0] == 0 else "o"
        cv2.putText(image, message, (0, 10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0), 2)

print("true: ", true)


# freeze model
import tensorflow as tf
from tensorflow.python.framework.graph_util import convert_variables_to_constants

checkpoint_path = "data/model-30"
with tf.Graph().as_default():
    X = tf.placeholder(tf.float32, [None, 50, 50, 1], name="normalized_gray_image")
    output_0 = simple_model(X, training=False)
    saver = tf.train.Saver()
    init = tf.global_variables_initializer()
    with tf.Session(config=tf.ConfigProto(log_device_placement=True)) as sess:
        sess.run(init)
        saver.restore(sess, checkpoint_path)
        minimal_graph = convert_variables_to_constants(sess, sess.graph_def, ["final_output"])
        tf.io.write_graph(minimal_graph, '.', 'object_detection/model.pb', as_text=False)
