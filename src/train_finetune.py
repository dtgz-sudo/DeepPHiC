import json
import argparse
import numpy as np
from utils import *
import tensorflow as tf
from DeepPHiC import DeepPHiC

def train(tissues, args):

    for tissue in tissues:

        ########## load files ##########
        print(tissue, 'loading files...')
        x1_seq, x2_seq, x1_read, x2_read, x1_dist, x2_dist, y = get_features(
            tissue,
            args.type
        )

        base_model = tf.keras.models.load_model(
            '../models/shared/DeepPHiC_{}_{}.h5'.format(tissue, args.type)
        )

        ########## train-test-val split ##########
        # 70% train, 15% val, 15% test
        N = len(x1_seq)
        train_idx, val_idx, test_idx = get_split(N)

        ########## data normalization ##########
        x1_read = normalize(x1_read, train_idx)
        x2_read = normalize(x2_read, train_idx)

        x1_dist = normalize(x1_dist, train_idx)
        x2_dist = normalize(x2_dist, train_idx)

        ########## train models ##########
        print(f'training DeepPHiC...')
        np.random.seed(0)
        model = DeepPHiC(learning_rate=args.lr, dropout=args.dropout)
        model.model.set_weights(base_model.get_weights())

        # only fine-tune the classifier
        if not args.train_full:
            for layer in model.model.layers[:-3]:
                layer.trainable = False

        # model.fit(
        #     x1_seq[train_idx], x2_seq[train_idx],
        #     x1_read[train_idx], x2_read[train_idx],
        #     x1_dist[train_idx], x2_dist[train_idx], y[train_idx],
        #     validation_data=(
        #         [x1_seq[val_idx], x2_seq[val_idx],
        #         x1_read[val_idx], x2_read[val_idx],
        #         x1_dist[val_idx], x2_dist[val_idx]], y[val_idx]
        #     ),
        #     epochs=args.epochs
        # )
        y_hat = model.predict(
            x1_seq[test_idx], x2_seq[test_idx],
            x1_read[test_idx], x2_read[test_idx],
            x1_dist[test_idx], x2_dist[test_idx]
        )
        stats = get_stats(y[test_idx], y_hat)

        # ########## save results ##########
        # RESULT_FILE = '../results/stats/DeepPHiC_finetune_{}_{}.json'.format(
        #     tissue, args.type
        # )
        # with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        #     json.dump(stats, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for training.')
    parser.add_argument(
        '--type', default='pp', type=str, choices=['pe', 'pp'],
        help='interaction type'
    )
    parser.add_argument(
        '--epochs', default=200, type=int, help='maximum training epochs'
    )
    parser.add_argument(
        '--lr', default=1e-4, type=int, help='learning rate'
    )
    parser.add_argument(
        '--dropout', default=0.2, type=float, help='dropout'
    )
    parser.add_argument(
        '--train_full', default=True, type=bool,
        help='whether to fine-tune only the classifier or entire model'
    )
    parser.add_argument(
        '--test', default=True, type=bool,
        help='test flag to work on sample data'
    )
    args = parser.parse_args()

    if args.test:
        tissues = ['AO', 'CM', 'LV', 'RV']
    else:
        with open('../res/tissues.json', 'r') as f:
            if args.type == 'pe':
                tissues = json.load(f)['pe']
            else:
                tissues = json.load(f)['pp']

    train(tissues, args)
    print('done')
