import sys
import time
import os
import argparse
import torch
import torch.nn as nn
import numpy as np
import torch.nn.functional as Fx
import torch.nn.init as init
import torch.utils.data
from torch.autograd import Variable
import torch.optim as optim
from torchvision import transforms, utils
from numpy import newaxis
import torch.nn.parallel
import torch.nn.functional
import cmetrics as metric
import random


class NET(nn.Module):

    # glplfun - global pooling function as nn.functional
    def __init__(self,nclass):
        super(NET,self).__init__()
        self.globalpool = Fx.avg_pool2d
        self.layer1 = nn.Sequential(nn.Conv2d(1,16,kernel_size=3,padding=1),nn.BatchNorm2d(16),nn.ReLU())
        self.layer2 = nn.Sequential(nn.Conv2d(16,16,kernel_size=3,padding=1),nn.BatchNorm2d(16),nn.ReLU())
        self.layer3 = nn.MaxPool2d(2)

        self.layer4 = nn.Sequential(nn.Conv2d(16,32,kernel_size=3,padding=1),nn.BatchNorm2d(32),nn.ReLU())
        self.layer5 = nn.Sequential(nn.Conv2d(32,32,kernel_size=3,padding=1),nn.BatchNorm2d(32),nn.ReLU())
        self.layer6 = nn.MaxPool2d(2)

        self.layer7 = nn.Sequential(nn.Conv2d(32,64,kernel_size=3,padding=1),nn.BatchNorm2d(64),nn.ReLU())
        self.layer8 = nn.Sequential(nn.Conv2d(64,64,kernel_size=3,padding=1),nn.BatchNorm2d(64),nn.ReLU())
        self.layer9 = nn.MaxPool2d(2)

        self.layer10 = nn.Sequential(nn.Conv2d(64,128,kernel_size=3,padding=1),nn.BatchNorm2d(128),nn.ReLU())
        self.layer11 = nn.Sequential(nn.Conv2d(128,128,kernel_size=3,padding=1),nn.BatchNorm2d(128),nn.ReLU())
        self.layer12 = nn.MaxPool2d(2)

        self.layer13 = nn.Sequential(nn.Conv2d(128,256,kernel_size=3,padding=1),nn.BatchNorm2d(256),nn.ReLU())
        self.layer14 = nn.Sequential(nn.Conv2d(256,256,kernel_size=3,padding=1),nn.BatchNorm2d(256),nn.ReLU())
        self.layer15 = nn.MaxPool2d(2)

        self.layer16 = nn.Sequential(nn.Conv2d(256,512,kernel_size=3,padding=1),nn.BatchNorm2d(512),nn.ReLU())
        self.layer17 = nn.MaxPool2d(2) # shape for 128 X 128 -- 2 X 2 -- reduction by factor 128/2 -- hop=64

        self.layer18 = nn.Sequential(nn.Conv2d(512,1024,kernel_size=2),nn.BatchNorm2d(1024),nn.ReLU())
        self.layer19 = nn.Sequential(nn.Conv2d(1024,nclass,kernel_size=1),nn.Sigmoid())

    def forward(self,x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.layer5(out)
        out = self.layer6(out)
        out = self.layer7(out)
        out = self.layer8(out)
        out = self.layer9(out)
        out = self.layer10(out)
        out = self.layer11(out)
        out = self.layer12(out)
        out = self.layer13(out)
        out = self.layer14(out)
        out = self.layer15(out)
        out = self.layer16(out)
        out = self.layer17(out)
        out = self.layer18(out)
        out1 = self.layer19(out)
        out = self.globalpool(out1,kernel_size=out1.size()[2:])
        out = out.view(out.size(0),-1)
        return out 

    def xavier_init(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                init.xavier_uniform(m.weight, gain=nn.init.calculate_gain('relu'))
                m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

use_cuda = torch.cuda.is_available()


def iterate_minibatches_torch(inputs,batchsize,targets=None,shuffle=False,last_batch=True):
    last_batch = not last_batch
    if targets is None:
        print 'No Target given to minibatch iterator. Using a dummy target with two outputs'
        targets = np.zeros((inputs.shape[0],2))
        
     
    inputs = torch.Tensor(inputs)
    targets = torch.Tensor(targets)
    
    dataset = torch.utils.data.TensorDataset(inputs,targets)
    dataiter = torch.utils.data.DataLoader(dataset,batch_size=batchsize,shuffle=shuffle,drop_last=last_batch)
    return dataiter


def dataloader(features_path,file_list,index,batch_size,feat_dim):
        if index+batch_size < len(file_list):
                current_batch_files = file_list[index:index+batch_size]
        else:
                current_batch_files = file_list[index:]
        X_train = []
        Y_train = []
        for item in current_batch_files:
                filename = item[0] 
                classname = item[1].strip()
                classname = classname.split(',')
                complete_filename = features_path + '/' + filename 
                #starttime_a = time.time()                      
                features = np.load(complete_filename)                      
                X_train_one = (np.hstack([features,np.zeros([args.spec_count,feat_dim-features.shape[1]])])).T                     
                X_train_one = X_train_one[newaxis,:,:]
                X_train.append(X_train_one)
                Y_train_this = np.zeros(args.classCount)
                classname_int = [int(i) for i in classname]
                Y_train_this[classname_int] =1
                Y_train.append(Y_train_this)        
        X_train = np.array(X_train)
        return X_train,Y_train
        

def read_file(filename,listname):
        with open(filename,'r') as f:
                lines = f.readlines()
                for line in lines:
                        listname.append((line.split(' ')[0],line.split(' ')[1]))
                f.close()
        return listname

def retrieve_index(number,range_list1):
        range_list1.sort()
        for ind in range(len(range_list1)):
                if number >= range_list1[ind] and number < range_list1[ind+1]: 
                        return ind+1
                elif number < range_list1[ind]:
                        return ind
                else:
                        continue


class Logger(object):
    def __init__(self,run_number):
        self.run_number = run_number
        self.terminal = sys.stdout
        self.log = open("logfiles/logfile_" + str(run_number) + "_gpu_latest_mel.log", "a")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  
    def flush(self):
        pass    


def setupClassifier(training_input_directory,validation_input_directory,testing_input_directory,classCount,spec_count,segment_length,learning_rate,output_path):
        
        sys.stdout = c1
        training_set_file_list = []
        testing_set_file_list = []
        validation_set_file_list = []

        for i in range(len(args.train_list)):
                training_set_file_list.append(args.train_test_split_path + '/b_' + str(args.train_list[i]) + '_training.list')
        for i in range(len(args.val_test_list)):
                testing_set_file_list.append(args.train_test_split_path + '/b_' + str(args.val_test_list[i]) + '_testing.list')
        for i in range(len(args.val_test_list)):
                validation_set_file_list.append(args.train_test_split_path + '/b_' + str(args.val_test_list[i]) + '_validation.list')

        training_set = [[] for x in range(len(args.train_list))]
        testing_set = [[] for x in range(len(args.val_test_list))]
        validation_set = [[] for x in range(len(args.val_test_list))]

        for i in range(len(args.train_list)):
                training_set[i] = read_file(training_set_file_list[i],training_set[i])
        for i in range(len(args.val_test_list)):
                validation_set[i] = read_file(validation_set_file_list[i],validation_set[i])
        for i in range(len(args.val_test_list)):
                testing_set[i] = read_file(testing_set_file_list[i],testing_set[i])


        # 864.txt, 768.txt, 672.txt, 576.txt, 480.txt, 288.txt 
        split_point= [10,1,1,1,1,1]
        #batch sizes 2592, 2304, 2016, 1728, 1440, 1152, 864, 576, 288
	split_point_training = [10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]

        length_training = []
        for i in range(len(args.train_list)):
                length_training.append(len(training_set[i]))
        length_training_sum = np.cumsum(length_training)

        length_testing = []
        for i in range(len(args.val_test_list)):
                length_testing.append(len(testing_set[i]))
        length_testing_sum = np.cumsum(length_testing)

        length_validation = []
        for i in range(len(args.val_test_list)):
                length_validation.append(len(validation_set[i]))
        length_validation_sum = np.cumsum(length_validation)


        net = NET(classCount)
        net.xavier_init()
        optimizer = optim.Adam(net.parameters(), lr=args.learning_rate)
        loss_fn = nn.BCELoss()
        if use_cuda:
                net.cuda()
                net = torch.nn.DataParallel(net, device_ids=range(torch.cuda.device_count()))
                #net = torch.nn.DataParallel(net, device_ids=[0,1])
                
        for epoch in range(args.num_epochs):
                print "Current epoch is " + str(epoch)
                i = 0
                j = 0
                epo_train_loss = 0
                batch_count = 0
                start_time = time.time()
                
                #############
                ### Training 
                #############
                
                print sum(length_training)
                net.train()
                while(i<sum(length_training)):
                        if (j == 0):
                            index1 = retrieve_index(i,length_training_sum)
                            print "INDEX 1 is "
                            print index1
                            print "i - " + str(index1) + "    length training sum " + str(length_training_sum[index1])
                            length = length_training[index1]
                            batch_size = length/split_point_training[index1]
                            training_files = training_set[index1]
                            random.shuffle(training_files)
                            feat_dim = int(args.train_list[index1])
                            
                        starttime1 = time.time()                        
                        X_train,Y_train=dataloader(training_input_directory,training_files,j,batch_size,feat_dim)
                        print "Train Data is loaded"
                        print "Value of J is = " + str(j)
                        print "Value of I is = " + str(i)
                        print "Value of length = " + str(length)
                        duration = time.time() - starttime1
                        print "Loading data took = " + str(duration)


                        if (j+batch_size) < length:
                            j = j+batch_size
                            i = i+batch_size
                        else:
                            j = 0
                            i = length_training_sum[index1]
                            print i
                            
                        for batch in  iterate_minibatches_torch(X_train,args.sgd_batch_size,Y_train,shuffle=True,last_batch=True):
                            indata,lbdata = batch
                                
                            if use_cuda:
                                indata = Variable(indata).cuda()
                                lbdata = Variable(lbdata).cuda()
                            else:
                                indata = Variable(indata)
                                lbdata = Variable(lbdata)
                                
                            optimizer.zero_grad()
                            batch_pred = net(indata)

                            batch_train_loss = loss_fn(batch_pred,lbdata)
                            batch_train_loss.backward()
                            optimizer.step()

                            epo_train_loss += batch_train_loss.data[0]
                            batch_count += 1
                        print batch_count
                        print "{} Set-Batch training done in {} seconds. Train Loss {} ".format(i, time.time() - start_time, epo_train_loss)
                epo_train_loss = epo_train_loss/batch_count

                print "{} Training done in {} seconds. Training Loss {}".format(epoch, time.time() - start_time, epo_train_loss)
                if not os.path.exists('model_'+str(args.run_number)):
                        os.mkdir('model_' + str(args.run_number))
                torch.save(net.state_dict(),'model_' + str(args.run_number)+'/model_path.' + str(args.run_number) + '_' +str(epoch)+  '.pkl')


                ###############
                ### Validation 
                ###############

                i = 0
                epo_val_loss = 0
                val_batch_count = 0
                start_time_val = time.time()
                all_predictions = np.random.rand(1,classCount)
                all_labels = np.zeros((1,classCount))
                net.eval()
                j = 0
                while(i<sum(length_validation)):
                        if (j==0):
                            index1 = retrieve_index(i,length_validation_sum)
                            print index1
                            print "i - " + str(index1) + "    length validation sum " + str(length_validation_sum[index1])
                            length = length_validation[index1]
                            batch_size = length/split_point[index1]
                            feat_dim = int(args.val_test_list[index1])
                            validation_files = validation_set[index1]
                            random.shuffle(validation_files)    
                        
                        X_val,Y_val=dataloader(validation_input_directory,validation_files,j,batch_size,feat_dim)
                        print "Validation Data is loaded"
                        print "Value of J is = " + str(j)
                        print "Value of I is = " + str(i)
                        print "Value of length = " + str(length)
                        if (j+batch_size) < length:
                            j = j+batch_size
                            i = i+batch_size
                        else:
                            j = 0
                            i = length_validation_sum[index1]
                            print "At length validation sum"
                            print i
                                
                        for batch in  iterate_minibatches_torch(X_val,args.sgd_batch_size,Y_val,shuffle=True,last_batch=True):
                            indata,lbdata = batch
                                
                            if use_cuda:
                                indata = Variable(indata,volatile=True).cuda()
                                lbdata = Variable(lbdata,volatile=True).cuda()
                            else:
                                indata = Variable(indata,volatile=True)
                                lbdata = Variable(lbdata,volatile=True)
                                
                            batch_pred = net(indata)

                            batch_val_loss = loss_fn(batch_pred,lbdata)
                            epo_val_loss += batch_val_loss.data[0]
                            val_batch_count += 1
                                
                            inres = batch_pred.data.cpu().numpy()
                            all_predictions = np.concatenate((all_predictions,inres),axis=0)
                            all_labels = np.concatenate((all_labels,lbdata.data.cpu().numpy()),axis=0)
                        print val_batch_count
                        print "{} Set-Batch Validation done in {} seconds. Validation Loss {} ".format(i, time.time() - start_time_val, epo_val_loss)
                epo_val_loss = epo_val_loss/val_batch_count
                all_predictions = all_predictions[1:,:]
                all_labels = all_labels[1:,:]
                print len(all_labels)
                
                aps = metric.compute_AP_all_class(all_labels,all_predictions)
                aucs = metric.compute_AUC_all_class(all_labels,all_predictions)
                aps_ranked = metric.compute_AP_my_all_class(all_labels,all_predictions)
                print "Epoch number " + str(epoch)
                print "Val aps ranked " + str(aps_ranked[-1])
                print "Val APS " + str(aps[-1])
                print "Val AUC " + str(aucs[-1])
                

                filename = os.path.join('metrics_' + str(args.run_number),'metrics_validation_' + str(args.run_number) + '_' +  str(epoch) + '_aps.txt')
                filename1 = os.path.join('metrics_' + str(args.run_number),'metrics_validation_' + str(args.run_number) + '_' + str(epoch) + '_aps_ranked.txt')
                filename2 = os.path.join('metrics_' + str(args.run_number),'metrics_validation_' + str(args.run_number) + '_' + str(epoch) + '_aucs.txt')

                if not os.path.isdir(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                
                np.save(filename,aps)
                np.save(filename1,aps_ranked)
                np.save(filename2,aucs)

                print "{} Validation done in {} seconds. Validation Loss {}".format(epoch, time.time() - start_time_val, epo_val_loss)

        ###############
        ### Testing 
        ###############

        i = 0
        epo_test_loss = 0
        test_batch_count = 0
        start_time_test = time.time()
        all_predictions = np.random.rand(1,classCount)
        all_labels = np.zeros((1,classCount))
        net.eval()
        j = 0
        while(i<sum(length_testing)):
                if (j==0):
                    index1 = retrieve_index(i,length_testing_sum)
                    print index1
                    print "i - " + str(index1) + "    length testing sum " + str(length_testing_sum[index1])
                    length = length_testing[index1]
                    batch_size = length/split_point[index1]
                    feat_dim = int(args.val_test_list[index1])
                    testing_files = testing_set[index1]
                    random.shuffle(testing_files)
                
                X_test,Y_test=dataloader(testing_input_directory,testing_files,j,batch_size,feat_dim)
                print "Test Data is loaded"
                print "Value of J is = " + str(j)
                print "Value of I is = " + str(i)
                print "Value of length = " + str(length)
                if (j+batch_size) < length:
                    j = j+batch_size
                    i = i+batch_size
                else:
                    j = 0
                    i = length_testing_sum[index1]
                    print "At length testing sum"
                    print i
                        
                for batch in  iterate_minibatches_torch(X_test,args.sgd_batch_size,Y_test,shuffle=True,last_batch=True):
                    indata,lbdata = batch
                        
                    if use_cuda:
                        indata = Variable(indata,volatile=True).cuda()
                        lbdata = Variable(lbdata,volatile=True).cuda()
                    else:
                        indata = Variable(indata,volatile=True)
                        lbdata = Variable(lbdata,volatile=True)
                        
                    batch_pred = net(indata)

                    batch_test_loss = loss_fn(batch_pred,lbdata)
                    epo_test_loss += batch_test_loss.data[0]
                    test_batch_count += 1
                        
                    inres = batch_pred.data.cpu().numpy()
    
                    all_predictions = np.concatenate((all_predictions,inres),axis=0)
                    all_labels = np.concatenate((all_labels,lbdata.data.cpu().numpy()),axis=0)
                print test_batch_count
                print "{} Set-Batch Testing done in {} seconds. Testing Loss {}".format(i, time.time() - start_time_test, epo_test_loss)
        print "Length of all prediction - Test " + str(len(all_predictions))
        all_predictions = all_predictions[1:,:]
        all_labels = all_labels[1:,:]
        aps = metric.compute_AP_all_class(all_labels,all_predictions)
        aucs = metric.compute_AUC_all_class(all_labels,all_predictions)
        aps_ranked = metric.compute_AP_my_all_class(all_labels,all_predictions)
                
        print "Test APS " + str(aps[-1])
        print "Test aps ranked " + str(aps_ranked[-1])
        print "Test AUCS " + str(aucs[-1])
        filename = 'metrics_testing_' + str(args.run_number) + 'aps.txt'
        filename1 = 'metrics_testing_' + str(args.run_number) + 'aps_ranked.txt'
        filename2 = 'metrics_testing_' + str(args.run_number) + 'aucs.txt'
        np.save(filename,aps)
        np.save(filename1,aps_ranked)
        np.save(filename2,aucs)

        epo_test_loss = epo_test_loss/test_batch_count

        print "{} Testing done in {} seconds. Testing Loss {}".format(epoch, time.time() - start_time_test,epo_test_loss)


if __name__ == '__main__':
        print len(sys.argv )
        if len(sys.argv) < 13:
                print "Running Instructions:\n\npython cnn.py <input_dir> <classCount> <spec_count> <segment_length> <learning_rate> <momentum> <evaluate> <test> <output_dir>"
        else:
                parser = argparse.ArgumentParser()

                parser.add_argument('--training_features_directory', type=str, default='training_directory', metavar='N',
                                    help='training_features_directory (default: training_directory')
                parser.add_argument('--validation_features_directory', type=str, default='validation_directory', metavar='N',
                                    help='validation_features_directory (default: validation_directory')
                parser.add_argument('--testing_features_directory', type=str, default='testing_directory', metavar='N',
                                    help='testing_features_directory (default: testing_directory')
                parser.add_argument('--classCount', type=int, default='18', metavar='N',
                                    help='classCount - default:18')
                parser.add_argument('--spec_count', type=int, default='96', metavar='N',
                                    help='spec_count - default:96')
                parser.add_argument('--segment_length', type=int, default='101', metavar='N',
                                    help='segment_length (default: 101)')
                parser.add_argument('--output_path', type=str, default='outputpath', metavar='N',
                                    help='output_path - default:outputpath')
                parser.add_argument('--learning_rate', type=float, default='0.001', metavar='N',
                                    help='learning_rate - default:0.001')
                parser.add_argument('--num_epochs', type=int, default='1', metavar='N',
                                    help='num_epochs - default:1')
                parser.add_argument('--sgd_batch_size', type=int, default='72', metavar='N',
                                    help='sgd_batch_size- default:40')
                parser.add_argument('--momentum', default=0.9, type=float, metavar='M', help='momentum')
                parser.add_argument('--evaluate', dest='evaluate', action='store_true', help='evaluate model on validation set')
                parser.add_argument('--test', dest='test', action='store_true', help='evaluate model on test set')
                parser.add_argument('--val_test_list',nargs='+', help='<Required>set flag',required=True)
                parser.add_argument('--train_list',nargs='+', help='<Required>set flag',required=True)
                parser.add_argument('--train_test_split_path',type=str,default='train_test_split',metavar='N',
                                   help='train_test_split_path - default train_test_split_path')
                parser.add_argument('--run_number', type=str, default='0', metavar='N',
                                    help='run_number- default:0')

                args = parser.parse_args()
                c1 = Logger(args.run_number)

                if not os.path.exists(args.output_path):
                        os.makedirs(args.output_path)


                setupClassifier(args.training_features_directory, args.validation_features_directory, args.testing_features_directory, args.classCount, args.spec_count, args.segment_length,args.learning_rate,args.output_path)

