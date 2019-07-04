import numpy as np
import cv2
import os

# Building 'AlexNet';
def create_alexnet(num_classes):
    network = input_data(shape=[None, config.IMAGE_SIZE, config.IMAGE_SIZE, 3])
    # 4维输入张量, 卷积核个数, 卷积核尺寸, 步长;
    network = conv_2d(network, 96, 11, strides=4, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    # 数据归一化, AlexNet的LRN层;
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 5, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = conv_2d(network, 384, 3, activation='relu')
    network = conv_2d(network, 384, 3, activation='relu')
    network = conv_2d(network, 256, 3, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    # 前5层大卷积层构建完毕;
    network = fully_connected(network, 4096, activation='tanh')
    network = dropout(network, 0.5)
    network = fully_connected(network, 4096, activation='tanh')
    network = dropout(network, 0.5)
    network = fully_connected(network, num_classes, activation='softmax')
    momentum = tflearn.Momentum(learning_rate=0.001, lr_decay=0.95, decay_step=200)
    network = regression(network, optimizer=momentum, loss='categorical_crossentropy')
    return network

# Use a already trained alexnet with the last layer redesigned
def create_alexnet(num_classes, restore=False):
    # Building 'AlexNet'
    network = input_data(shape=[None, config.IMAGE_SIZE, config.IMAGE_SIZE, 3])
    network = conv_2d(network, 96, 11, strides=4, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 5, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = conv_2d(network, 384, 3, activation='relu')
    network = conv_2d(network, 384, 3, activation='relu')
    network = conv_2d(network, 256, 3, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = fully_connected(network, 4096, activation='tanh')
    network = dropout(network, 0.5)
    network = fully_connected(network, 4096, activation='tanh')
    network = dropout(network, 0.5)
    # Do not restore this layer;
    network = fully_connected(network, num_classes, activation='softmax', restore=restore)
    network = regression(network, optimizer='momentum', loss='categorical_crossentropy', learning_rate=0.001)
    return network

# Use a already trained alexnet with the last layer redesigned
# 减去softmax输出层，获得图片的特征
def create_alexnet():
    # Building 'AlexNet'
    network = input_data(shape=[None, config.IMAGE_SIZE, config.IMAGE_SIZE, 3])
    network = conv_2d(network, 96, 11, strides=4, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 5, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = conv_2d(network, 384, 3, activation='relu')
    network = conv_2d(network, 384, 3, activation='relu')
    network = conv_2d(network, 256, 3, activation='relu')
    network = max_pool_2d(network, 3, strides=2)
    network = local_response_normalization(network)
    network = fully_connected(network, 4096, activation='tanh')
    network = dropout(network, 0.5)
    network = fully_connected(network, 4096, activation='tanh')
    # 连Dropout和Softmax层也没了;
    network = regression(network, optimizer='momentum', loss='categorical_crossentropy', learning_rate=0.001)
    return network

# 加载数据;
def load_data(datafile, num_class, save=False, save_path='dataset.pkl'):
    fr = codecs.open(datafile, 'r', 'utf-8')
    train_list = fr.readlines()
    labels = []
    images = []
    # 对每一个训练样本
    for line in train_list:
        tmp = line.strip().split(' ')
        fpath = tmp[0]
        img = cv2.imread(fpath)
        # 样本resize到227x227，转为矩阵保存
        img = prep.resize_image(img, config.IMAGE_SIZE, config.IMAGE_SIZE)
        np_img = np.asarray(img, dtype="float32")
        images.append(np_img)
        # 处理相应标签;
        index = int(tmp[1])
        label = np.zeros(num_class)
        label[index] = 1
        labels.append(label)
    if save:
        # 序列化保存
        pickle.dump((images, labels), open(save_path, 'wb'))
    fr.close()
    # (图像,标签)对;
    return images, labels


# Training;
def train(network, X, Y, save_model_path):
    model = tflearn.DNN(network, checkpoint_path='model_alexnet',
                        max_checkpoints=1, tensorboard_verbose=2, tensorboard_dir='output')
    if os.path.isfile(save_model_path + '.index'):
        # 前提是模型结构一样;
        model.load(save_model_path)
        print('load model...')

    model.fit(X, Y, n_epoch=200, validation_set=0.1, shuffle=True,
              show_metric=True, batch_size=64, snapshot_step=200,
              snapshot_epoch=False, run_id='alexnet_oxflowers17') # epoch = 1000
    # Save the model
    model.save(save_model_path)
    print('save model...')

# 精调AlexNet: 从已经预训练的权重中更进一步调整;
def fine_tune_Alexnet(network, X, Y, save_model_path, fine_tune_model_path):
    # Training
    model = tflearn.DNN(network, checkpoint_path='rcnn_model_alexnet',
                        max_checkpoints=1, tensorboard_verbose=2, tensorboard_dir='output_RCNN')
    if os.path.isfile(fine_tune_model_path + '.index'):
        print("Loading the fine tuned model")
        model.load(fine_tune_model_path)
        # 加载预训练好的模型参数
    elif os.path.isfile(save_model_path + '.index'):
        print("Loading the alexnet")
        model.load(save_model_path)
    else:
        print("No file to load, error")
        return False
    
    # 再已有预训练权重的基础上再进行fit(), 谓之"精调";
    model.fit(X, Y, n_epoch=3, validation_set=0.1, shuffle=True,
              show_metric=True, batch_size=64, snapshot_step=200,
              snapshot_epoch=False, run_id='alexnet_rcnnflowers2')
    # Save the model;
    model.save(fine_tune_model_path)


# Read in data and save data for AlexNet;
def load_train_proposals(datafile, num_class, save_path, threshold=0.5, is_svm=False, save=False):
    fr = open(datafile, 'r')
    train_list = fr.readlines()
    # random.shuffle(train_list)
    for num,line in enumerate(train_list):
        labels = []
        images = []
        rects  = []
        tmp = line.strip().split(' ')
        # tmp0 = image address
        # tmp1 = label
        # tmp2 = rectangle vertices
        img_path = tmp[0]
        img = cv2.imread(tmp[0])
        # 选择搜索得到候选框;
        img_lbl, regions = selective_search(img_path, neighbor=8, scale=500, sigma=0.9, min_size=20)
        candidates = set()
        ref_rect = tmp[2].split(',')
        ref_rect_int = [int(i) for i in ref_rect]
        Gx = ref_rect_int[0]
        Gy = ref_rect_int[1]
        Gw = ref_rect_int[2]
        Gh = ref_rect_int[3]
        # regions是什么数据格式/形式, r['rect']是什么;
        for r in regions:
            # excluding same rectangle (with different segments)
            if r['rect'] in candidates:
                continue
            # excluding small regions
            if r['size'] < 220:
                continue
            if (r['rect'][2] * r['rect'][3]) < 500:
                continue
            # 截取目标区域
            proposal_img, proposal_vertice = clip_pic(img, r['rect'])
            # Delete Empty array
            if len(proposal_img) == 0:
                continue
            # Ignore things contain 0 or not C contiguous array
            x, y, w, h = r['rect']
            if w == 0 or h == 0:
                continue
            # Check if any 0-dimension exist
            [a, b, c] = np.shape(proposal_img)
            if a == 0 or b == 0 or c == 0:
                continue
            # Resize to 227*227;
            resized_proposal_img = resize_image(proposal_img, config.IMAGE_SIZE, config.IMAGE_SIZE)
            candidates.add(r['rect'])
            img_float = np.asarray(resized_proposal_img, dtype="float32")
            images.append(img_float)
            # 计算IOU;
            iou_val = IOU(ref_rect_int, proposal_vertice)
            # x,y,w,h作差，用于boundingbox回归
            rects.append([(Gx-x)/w, (Gy-y)/h, math.log(Gw/w), math.log(Gh/h)])
            # propasal_rect = [proposal_vertice[0], proposal_vertice[1], proposal_vertice[4], proposal_vertice[5]]
            # print(iou_val)
            # labels, let 0 represent default class, which is background
            index = int(tmp[1])
            if is_svm:
                # iou小于阈值，为背景，0
                if iou_val < threshold:
                    labels.append(0)
                elif  iou_val > 0.6: # 0.85
                    labels.append(index)
                else:
                    labels.append(-1)
            else:
                label = np.zeros(num_class + 1)
                if iou_val < threshold:
                    label[0] = 1
                else:
                    label[index] = 1
                labels.append(label)

        if is_svm:
            ref_img, ref_vertice = clip_pic(img, ref_rect_int)
            resized_ref_img = resize_image(ref_img, config.IMAGE_SIZE, config.IMAGE_SIZE)
            img_float = np.asarray(resized_ref_img, dtype="float32")
            images.append(img_float)
            rects.append([0, 0, 0, 0])
            labels.append(index)
        tools.view_bar("processing image of %s" % datafile.split('\\')[-1].strip(), num + 1, len(train_list))

        # 保存这些计算出来的proposal regions;
        if save:
            if is_svm:
                # strip()去除首位空格
                np.save((os.path.join(save_path, tmp[0].split('/')[-1].split('.')[0].strip()) + '_data.npy'), [images, labels, rects])
            else:
                # strip()去除首位空格
                np.save((os.path.join(save_path, tmp[0].split('/')[-1].split('.')[0].strip()) + '_data.npy'),
                        [images, labels])
    print(' ')
    fr.close()


# Construct cascade svms, 训练SVM分类器;
def train_svms(train_file_folder, model):
    files = os.listdir(train_file_folder)
    svms = []
    train_features = []
    bbox_train_features = []
    rects = []
    for train_file in files:
        if train_file.split('.')[-1] == 'txt':
            pred_last = -1
            pred_now = 0
            X, Y, R = generate_single_svm_train(os.path.join(train_file_folder, train_file))
            Y1 = []
            features1 = []
            Y_hard = []
            features_hard = []
            for ind, i in enumerate(X):
                # extract features 提取特征
                feats = model.predict([i])
                train_features.append(feats[0])
                # 所有正负样本加入feature1,Y1
                if Y[ind]>=0:
                    Y1.append(Y[ind])
                    features1.append(feats[0])
                    # 对与groundtruth的iou>0.6的加入boundingbox训练集
                    if Y[ind]>0:
                        bbox_train_features.append(feats[0])
                        rects.append(R[ind])
                # 剩下作为测试集
                else:
                    Y_hard.append(Y[ind])
                    features_hard.append(feats[0])
                tools.view_bar("extract features of %s" % train_file, ind + 1, len(X))

            # 难负例挖掘
            clf = SVC(probability=True)
            # 训练直到准确率不再提高
            while pred_now > pred_last:
                clf.fit(features1, Y1)
                features_new_hard = []
                Y_new_hard = []
                index_new_hard = []
                # 统计测试正确数量
                count = 0
                for ind, i in enumerate(features_hard):
                    # print(clf.predict([i.tolist()])[0])
                    if clf.predict([i.tolist()])[0] == 0:
                        count += 1
                    # 如果被误判为正样本，加入难负例集合
                    elif clf.predict([i.tolist()])[0] > 0:
                        # 找到被误判的难负例
                        features_new_hard.append(i)
                        Y_new_hard.append(clf.predict_proba([i.tolist()])[0][1])
                        index_new_hard.append(ind)
                # 如果难负例样本过少，停止迭代
                if len(features_new_hard)/10<1:
                    break
                pred_last = pred_now
                # 计算新的测试正确率
                pred_now = count / len(features_hard)
                # print(pred_now)
                # 难负例样本根据分类概率排序，取前10%作为负样本加入训练集
                sorted_index = np.argsort(-np.array(Y_new_hard)).tolist()[0:int(len(features_new_hard)/10)]
                for idx in sorted_index:
                    index = index_new_hard[idx]
                    features1.append(features_new_hard[idx])
                    Y1.append(0)
                    # 测试集中删除这些作为负样本加入训练集的样本。
                    features_hard.pop(index)
                    Y_hard.pop(index)

            print(' ')
            print("feature dimension")
            print(np.shape(features1))
            svms.append(clf)
            # 将clf序列化，保存svm分类器
            joblib.dump(clf, os.path.join(train_file_folder, str(train_file.split('.')[0]) + '_svm.pkl'))

    # 保存boundingbox回归训练集
    np.save((os.path.join(train_file_folder, 'bbox_train.npy')), [bbox_train_features, rects])
    # print(rects[0])
    return svms


# 训练boundingbox回归, 是线性回归模型, 根据Conv特征值拟合目标位置值: 如下将features和rects分别append到train变量中;
def train_bbox(npy_path):
    features, rects = np.load((os.path.join(npy_path, 'bbox_train.npy')))
    # 不能直接np.array()，应该把元素全部取出放入空列表中。因为features和rects建立时用的append，导致其中元素结构不能直接转换成矩阵
    X = []
    Y = []
    for ind, i in enumerate(features):
        X.append(i)
    X_train = np.array(X)

    for ind, i in enumerate(rects):
        Y.append(i)
    Y_train = np.array(Y)

    # 线性回归模型训练
    clf = Ridge(alpha=1.0)
    clf.fit(X_train, Y_train)
    # 序列化，保存bbox回归
    joblib.dump(clf, os.path.join(npy_path,'bbox_train.pkl'))
    return clf

# 此文件直接运行的运行代码块;
if __name__ == '__main__':
    train_file_folder = config.TRAIN_SVM
    img_path = './17flowers/jpg/16/image_1336.jpg'  # or './17flowers/jpg/16/****.jpg'
    image = cv2.imread(img_path)
    im_width = image.shape[1]
    im_height = image.shape[0]
    # print(im_width)
    # print(im_height)
    # 提取region proposal
    imgs, verts = image_proposal(img_path)
    tools.show_rect(img_path, verts)

    # 建立模型，网络
    net   = create_alexnet()
    model = tflearn.DNN(net)
    # 加载微调后的alexnet网络参数
    model.load(config.FINE_TUNE_MODEL_PATH)
    # 加载/训练svm分类器 和 boundingbox回归器
    svms = []
    bbox_fit = []
    # boundingbox回归器是否有存档
    bbox_fit_exit = 0
    # 加载svm分类器和boundingbox回归器
    for file in os.listdir(train_file_folder):
        if file.split('_')[-1] == 'svm.pkl':
            svms.append(joblib.load(os.path.join(train_file_folder, file)))
        if file == 'bbox_train.pkl':
            bbox_fit = joblib.load(os.path.join(train_file_folder, file))
            bbox_fit_exit = 1
    if len(svms) == 0:
        svms = train_svms(train_file_folder, model)
    if bbox_fit_exit == 0:
        bbox_fit = train_bbox(train_file_folder)

    print("Done fitting svms")
    features = model.predict(imgs)
    print("predict image:")
    # print(np.shape(features))
    results = []
    results_label = []
    results_score = []
    count = 0
    for f in features:
        for svm in svms:
            pred = svm.predict([f.tolist()])
            # not background
            if pred[0] != 0:
                # boundingbox回归
                bbox = bbox_fit.predict([f.tolist()])
                tx, ty, tw, th = bbox[0][0], bbox[0][1], bbox[0][2], bbox[0][3]
                px, py, pw, ph = verts[count]
                gx = tx * pw + px
                gy = ty * ph + py
                gw = math.exp(tw) * pw
                gh = math.exp(th) * ph
                if gx<0:
                    gw = gw - (0 - gx)
                    gx = 0
                if gx+gw > im_width:
                    gw = im_width - gx
                if gy<0:
                    gh = gh - (0-gh)
                    gy = 0
                if gy+gh > im_height:
                    gh = im_height - gy
                results.append([gx,gy,gw,gh])
                results_label.append(pred[0])
                results_score.append(svm.predict_proba([f.tolist()])[0][1])
        count += 1

    results_final = []
    results_final_label = []

    # 非极大抑制, 删除得分小于0.5的候选框;
    delete_index1 = []
    for ind in range(len(results_score)):
        if results_score[ind]<0.5:
            delete_index1.append(ind)
    num1 = 0
    for idx in delete_index1:
        results.pop(idx - num1)
        results_score.pop(idx - num1)
        results_label.pop(idx - num1)
        num1 += 1

    while len(results) > 0:
        # 找到列表中得分最高的
        max_index = results_score.index(max(results_score))
        max_x, max_y, max_w, max_h = results[max_index]
        max_vertice = [max_x, max_y, max_x+max_w, max_y+max_h, max_w, max_h]
        # 该候选框加入最终结果
        results_final.append(results[max_index])
        results_final_label.append(results_label[max_index])
        # 从results中删除该候选框
        results.pop(max_index)
        results_label.pop(max_index)
        results_score.pop(max_index)
        # print(len(results_score))
        # 删除与得分最高候选框iou>0.5的其他候选框
        delete_index = []
        for ind, i in enumerate(results):
            iou_val = IOU(i, max_vertice)
            if iou_val>0.5:
                delete_index.append(ind)
        num = 0
        for idx in delete_index:
            # print('\n')
            # print(idx)
            # print(len(results))
            results.pop(idx-num)
            results_score.pop(idx-num)
            results_label.pop(idx-num)
            num += 1

    print("result:")
    print(results_final)
    print("result label:")
    print(results_final_label)
    tools.show_rect(img_path, results_final)
