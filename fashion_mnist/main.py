
from matplotlib import pyplot
from keras.datasets import fashion_mnist 

def main():
    
    # load the images into memory
    (trainX, trainy), (testX, testy) = fashion_mnist.load_data()

    # summarize the shape of the dataset
    print('Train', trainX.shape, trainy.shape)
    print('Test', testX.shape, testy.shape)

    # plot images from the training dataset
    for i in range(100):
        # define subplot
        pyplot.subplot(10, 10, 1 + i)
        # turn off axis
        pyplot.axis('off')
        # plot raw pixel data
        pyplot.imshow(trainX[i], cmap='gray_r')

    pyplot.show()


if __name__ == '__main__':
    main()
