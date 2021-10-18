import importlib
import torch

from utils.meters import ScalarMeter


def get_lr_scheduler(optimizer, lr_scheduler_name, args):
    """ Get learning rate """
    if lr_scheduler_name == 'multistep':
        lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(
            optimizer, milestones=args.multistep_lr_milestones,
            gamma=args.multistep_lr_gamma)

    elif lr_scheduler_name == 'exp_decaying':
        lr_dict = {}
        for i in range(args.num_epochs):
            if i == 0:
                lr_dict[i] = 1
            else:
                lr_dict[i] = lr_dict[i - 1] * args.exp_decaying_lr_gamma

        def lr_lambda(epoch): return lr_dict[epoch]
        lr_scheduler = torch.optim.lr_scheduler.LambdaLR(
            optimizer, lr_lambda=lr_lambda)

    elif lr_scheduler_name == 'linear_decaying':
        lr_dict = {}
        for i in range(args.num_epochs):
            lr_dict[i] = 1. - i / args.num_epochs

        def lr_lambda(epoch): return lr_dict[epoch]
        lr_scheduler = torch.optim.lr_scheduler.LambdaLR(
            optimizer, lr_lambda=lr_lambda)

    elif lr_scheduler_name is None:
        lr_scheduler = None

    else:
        try:
            lr_scheduler_lib = importlib.import_module(lr_scheduler_name)
            return lr_scheduler_lib.get_lr_scheduler(optimizer)
        except ImportError:
            raise NotImplementedError(
                'Learning rate scheduler {} is not yet implemented.'.format(
                    lr_scheduler_name))
    return lr_scheduler


# See https://github.com/facebookresearch/maskrcnn-benchmark/ ...
#           ... blob/master/maskrcnn_benchmark/solver/build.py
def get_optimizer(model, optim, weight_decay, lr,):
    """ Get optimizer """

    if optim in ['adam', 'adamw']:
        torch_optim = (torch.optim.Adam if optim == 'adam' 
                       else torch.optim.AdamW)
        optimizer = torch_optim(model.parameters(), lr=lr,
                                    weight_decay=weight_decay)
    else:
        try:
            optimizer_lib = importlib.import_module(optim)
            return optimizer_lib.get_optimizer(model)
        except ImportError:
            raise NotImplementedError(
                'Optimizer {} is not yet implemented.'.format(optim))
    return optimizer


def get_meters(phase, topk, width_mult_list, slimmable=True):
    """ Util function for meters """
    if slimmable:
        meters_all = {}
        for width_mult in width_mult_list:
            meters = {}
            meters['loss'] = ScalarMeter('{}_loss/{}'.format(
                phase, str(width_mult)))
            for k in topk:
                meters['top{}_error'.format(k)] = ScalarMeter(
                    '{}_top{}_error/{}'.format(phase, k, str(width_mult)))
            meters_all[str(width_mult)] = meters
        meters = meters_all
    else:
        meters = {}
        meters['loss'] = ScalarMeter('{}_loss'.format(phase))
        for k in topk:
            meters['top{}_error'.format(k)] = ScalarMeter(
                '{}_top{}_error'.format(phase, k))
    return meters

