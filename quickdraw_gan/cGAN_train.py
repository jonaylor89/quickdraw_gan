import os
import numpy as np
from numpy import expand_dims
from numpy import zeros
from numpy import ones
from matplotlib import pyplot
from numpy.random import randn
from numpy.random import randint
from sklearn.model_selection import train_test_split

from keras.optimizers import Adam
from keras.models import Model
from keras.layers import Input
from keras.layers import Dense
from keras.layers import Reshape
from keras.layers import Flatten
from keras.layers import Conv2D
from keras.layers import Conv2DTranspose
from keras.layers import LeakyReLU
from keras.layers import Dropout
from keras.layers import Embedding
from keras.layers import Concatenate


# define the standalone discriminator model
def define_discriminator(in_shape=(28, 28, 1), n_classes=3):
    # label input
    in_label = Input(shape=(1,))

    # embedding for categorical input
    li = Embedding(n_classes, 50)(in_label)

    # scale up to image dimensions with linear activation
    n_nodes = in_shape[0] * in_shape[1]
    li = Dense(n_nodes)(li)

    # reshape to additional channel
    li = Reshape((in_shape[0], in_shape[1], 1))(li)

    # image input
    in_image = Input(shape=in_shape)

    # concat label as a channel
    merge = Concatenate()([in_image, li])

    # downsample
    fe = Conv2D(128, (3, 3), strides=(2, 2), padding="same")(merge)
    fe = LeakyReLU(alpha=0.2)(fe)

    # downsample
    fe = Conv2D(128, (3, 3), strides=(2, 2), padding="same")(fe)
    fe = LeakyReLU(alpha=0.2)(fe)

    # flatten feature maps
    fe = Flatten()(fe)

    # dropout
    fe = Dropout(0.4)(fe)

    # output
    out_layer = Dense(1, activation="sigmoid")(fe)

    # define model
    model = Model([in_image, in_label], out_layer)

    # compile model
    opt = Adam(lr=0.0002, beta_1=0.5)
    model.compile(loss="binary_crossentropy", optimizer=opt, metrics=["accuracy"])

    return model


# define the standalone generator model
def define_generator(latent_dim, n_classes=3):
    # label input
    in_label = Input(shape=(1,))

    # embedding for categorical input
    li = Embedding(n_classes, 50)(in_label)

    # linear multiplication
    n_nodes = 7 * 7
    li = Dense(n_nodes)(li)

    # reshape to additional channel
    li = Reshape((7, 7, 1))(li)

    # image generator input
    in_lat = Input(shape=(latent_dim,))

    # foundation for 7x7 image
    n_nodes = 128 * 7 * 7
    gen = Dense(n_nodes)(in_lat)
    gen = LeakyReLU(alpha=0.2)(gen)
    gen = Reshape((7, 7, 128))(gen)

    # merge image gen and label input
    merge = Concatenate()([gen, li])

    # upsample to 14x14
    gen = Conv2DTranspose(128, (4, 4), strides=(2, 2), padding="same")(merge)
    gen = LeakyReLU(alpha=0.2)(gen)

    # upsample to 28x28
    gen = Conv2DTranspose(128, (4, 4), strides=(2, 2), padding="same")(gen)
    gen = LeakyReLU(alpha=0.2)(gen)

    # output
    out_layer = Conv2D(1, (7, 7), activation="tanh", padding="same")(gen)

    # define model
    model = Model([in_lat, in_label], out_layer)

    return model


# define the combined generator and discriminator model, for updating the generator
def define_gan(g_model, d_model):

    # make weights in the discriminator not trainable
    d_model.trainable = False

    # get noise and label inputs from generator model
    gen_noise, gen_label = g_model.input

    # get image output from the generator model
    gen_output = g_model.output

    # connect image output and label input from generator as inputs to discriminator
    gan_output = d_model([gen_output, gen_label])

    # define gan model as taking noise and label and outputting a classification
    model = Model([gen_noise, gen_label], gan_output)

    # compile model
    opt = Adam(lr=0.0002, beta_1=0.5)
    model.compile(loss="binary_crossentropy", optimizer=opt)

    return model


# load quickdraw images
def load_real_samples():
    # load dataset
    trainX, _, trainY, _ = load_data()

    trainX = np.array(trainX)
    trainY = np.array(trainY)

    # expand to 3d, e.g. add channels
    # X = expand_dims(trainX, axis=-1)

    # convert to float32
    X = trainX.astype("float32")

    # scale from [0,255] to [-1,1]
    X = (X - 127.5) / 127.5

    return [X, trainY]


# select real samples
def generate_real_samples(dataset, n_samples):
    # split into images and labels
    images, labels = dataset

    # choose random instances
    ix = randint(0, images.shape[0], n_samples)

    # select images and labels
    X, labels = images[ix], labels[ix]

    # generate class labels
    y = ones((n_samples, 1))

    return [X, labels], y


# generate points in latent space as input for the generator
def generate_latent_points(latent_dim, n_samples, n_classes=3):
    # generate points in the latent space
    x_input = randn(latent_dim * n_samples)

    # reshape into a batch of inputs for the network
    z_input = x_input.reshape(n_samples, latent_dim)

    # generate labels
    labels = randint(0, n_classes, n_samples)

    return [z_input, labels]


# use the generator to generate n fake examples, with class labels
def generate_fake_samples(generator, latent_dim, n_samples):
    # generate points in latent space
    z_input, labels_input = generate_latent_points(latent_dim, n_samples)

    # predict outputs
    images = generator.predict([z_input, labels_input])

    # create class labels
    y = zeros((n_samples, 1))

    return [images, labels_input], y


def load_data():
    labels_mapping = {
        "apple": 0,
        "banana": 1,
        "grapes": 2
    }

    this_directory = os.path.dirname(os.path.realpath(__file__))
    quickdraw_directory = this_directory + "/quickdraw"
    bitmap_directory = quickdraw_directory + "/bitmap"
    training_samples = 10_000

    random_state = np.random.RandomState(100)

    labels, drawings = [], []

    for category in labels_mapping.keys():
        data = np.load(f"{bitmap_directory}/{category}.npy", allow_pickle=True)

        random_state.shuffle(data)
        sampled_data = data[:training_samples]

        transformed_data = sampled_data.reshape(sampled_data.shape[0], 28, 28, 1)

        # for pixel_data in sampled_data:
        for pixel_data in transformed_data:
            drawings.append(pixel_data)
            labels.append(labels_mapping[category])

        print(f"...{category} bitmaps complete")

    print(f"{len(drawings)} bitmaps with {len(labels)} labels")

    return train_test_split(drawings, labels, test_size=0.2)


# create a line plot of loss for the gan and save to file
def plot_history(d_hist, g_hist, a_hist):

	# plot loss
	pyplot.subplot(2, 1, 1)
	pyplot.plot(d_hist, label='dis')
	pyplot.plot(g_hist, label='gen')
	pyplot.legend()

	# plot discriminator accuracy
	pyplot.subplot(2, 1, 2)
	pyplot.plot(a_hist, label='acc')
	pyplot.legend()

	# save plot to file
	pyplot.savefig('results_convergence/plot_line_plot_loss.png')
	pyplot.close()


# generate samples and save as a plot and save the model
def summarize_performance(step, g_model, latent_dim, n_samples=100):
	# prepare fake examples
	X, _ = generate_fake_samples(g_model, latent_dim, n_samples)

	# scale from [-1,1] to [0,1]
	X = (X[0] + 1) / 2.0

	# plot images
	for i in range(10 * 10):

		# define subplot
		pyplot.subplot(10, 10, 1 + i)

		# turn off axis
		pyplot.axis('off')

		# plot raw pixel data
		pyplot.imshow(X[i, :, :, 0], cmap='gray_r')

	# save plot to file
	pyplot.savefig('results_convergence/generated_plot_%03d.png' % (step+1))
	pyplot.close()

	# save the generator model
	g_model.save('results_convergence/model_%03d.h5' % (step+1))
    

# train the generator and discriminator
def train(g_model, d_model, gan_model, dataset, latent_dim, n_epochs=1, n_batch=100):
    bat_per_epo = int(dataset[0].shape[0] / n_batch)
    half_batch = int(n_batch / 2)

    d1_hist = []
    d2_hist = []
    g_hist = []

    # manually enumerate epochs
    for i in range(n_epochs):

        # enumerate batches over the training set
        for j in range(bat_per_epo):

            # get randomly selected 'real' samples
            [X_real, labels_real], y_real = generate_real_samples(dataset, half_batch)

            # update discriminator model weights
            d_loss1, _ = d_model.train_on_batch([X_real, labels_real], y_real)

            # generate 'fake' examples
            [X_fake, labels], y_fake = generate_fake_samples(
                g_model, latent_dim, half_batch
            )

            # update discriminator model weights
            d_loss2, _ = d_model.train_on_batch([X_fake, labels], y_fake)

            # prepare points in latent space as input for the generator
            [z_input, labels_input] = generate_latent_points(latent_dim, n_batch)

            # create inverted labels for the fake samples
            y_gan = ones((n_batch, 1))

            # update the generator via the discriminator's error
            g_loss = gan_model.train_on_batch([z_input, labels_input], y_gan)

            # summarize loss on this batch

            print(
                f">{i + 1}, {j + 1}/{bat_per_epo}, d1={d_loss1:.3f}, d2={d_loss2:.3f} g={g_loss:.3f}"
            )

            # record history
            d1_hist.append(d_loss1)
            d2_hist.append(d_loss2)
            g_hist.append(g_loss)

        summarize_performance(i, g_model, latent_dim)

    plot_history(d1_hist, d2_hist, g_hist)

    # save the generator model
    g_model.save("cgan_doodle_generator.h5")


def main():
    os.makedirs('results_convergence', exist_ok=True)

    # size of the latent space
    latent_dim = 100

    # create the discriminator
    d_model = define_discriminator()

    # create the generator
    g_model = define_generator(latent_dim)

    # create the gan
    gan_model = define_gan(g_model, d_model)

    # load image data
    dataset = load_real_samples()

    # train model
    train(g_model, d_model, gan_model, dataset, latent_dim)


if __name__ == "__main__":
    main()
