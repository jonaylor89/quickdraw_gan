
from keras.datasets import fashion_mnist 

def main():
    
    # load the images into memory
    (trainX, trainy), (testX, testy) = fashion_mnist.load_data()

    # summarize the shape of the dataset
    print('Train', trainX.shape, trainy.shape)
    print('Test', testX.shape, testy.shape)


if __name__ == '__main__':
    main()
