import os
import glob
import json

seism_root = './seism'


def mkdir_if_missing(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def eval_edge_predictions_forward(save_dir, exp_name):
    """ The edge are evaluated through seism """

    print('Evaluate the edge prediction using seism ... This can take a while ...')

    # DataLoaders
    database = 'PASCALContext'

    # First check if all files are there
    files = glob.glob(os.path.join(save_dir, 'edge/*png'))
    assert (len(files) == 5105)

    # rsync the results to the seism root
    print('Rsync the results to the seism root ...')
    result_dir = os.path.join(seism_root, 'datasets/%s/%s/' % (database, exp_name))
    mkdir_if_missing(result_dir)
    os.system('rsync -a %s %s' % (os.path.join(save_dir, 'edge/*'), result_dir))
    print('Done ...')

    # generate a seism script that we will run.
    print('Generate seism script to perform the evaluation ...')
    seism_base = os.path.join('./pr_curves_base.m')
    with open(seism_base) as f:
        seism_file = f.readlines()
    seism_file = [line.strip() for line in seism_file]
    output_file = [seism_file[0]]

    ## Add experiments parameters (TODO)
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/scripts/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/misc/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/tests/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/gt_wrappers/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/io/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/measures/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/piotr_edges/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/segbench/'))]
    # output_file += ['addpath(\'%s\')' %(os.path.join(seism_root, 'src/piotr_toolbox/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/scripts/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/misc/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/tests/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/gt_wrappers/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/io/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/measures/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/piotr_edges/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/segbench/'))]
    output_file += ['addpath(\'%s\')' % (os.path.join('.', 'src/piotr_toolbox/'))]
    output_file += ['database = \'' + database + '\'']
    output_file.extend(seism_file[1:18])

    ## Add method (TODO)
    output_file += [
        'methods(end+1).name = \'%s\'; methods(end).io_func = @read_one_cont_png; methods(end).legend =     methods(end).name;  methods(end).type = \'contour\';' % (
            exp_name)]
    output_file.extend(seism_file[19:61])

    ## Add path to save output
    output_file += ['filename = \'%s\'' % (os.path.join(save_dir, database + '_' + 'test' + '_edge.txt'))]
    output_file += seism_file[62:]

    # save the file to the seism dir
    output_file_path = os.path.join(seism_root, exp_name + '.m')
    with open(output_file_path, 'w') as f:
        for line in output_file:
            f.write(line + '\n')

    # go to the seism dir and perform evaluation
    print('Go to seism root dir and run the evaluation ... This takes time ...')
    cwd = os.getcwd()
    os.chdir(seism_root)
    os.system("matlab -nodisplay -nosplash -nodesktop -r \"addpath(\'%s\');%s;exit\"" % ('.', exp_name))
    os.chdir(cwd)

    # write to json
    print('Finished evaluation in seism ... Write results to JSON ...')
    with open(os.path.join(save_dir, database + '_' + 'test' + '_edge.txt'), 'r') as f:
        seism_result = [line.strip() for line in f.readlines()]

    eval_dict = {}
    for line in seism_result:
        metric, score = line.split(':')
        eval_dict[metric] = float(score)

    with open(os.path.join(save_dir, database + '_' + 'test' + '_edge.json'), 'w') as f:
        json.dump(eval_dict, f)

    # print
    print('Edge Detection Evaluation')
    for k, v in eval_dict.items():
        spaces = ''
        for j in range(0, 10 - len(k)):
            spaces += ' '
        print('{0:s}{1:s}{2:.4f}'.format(k, spaces, 100 * v))

    # cleanup - Important. Else Matlab will reuse the files.
    print('Cleanup files in seism ...')
    result_rm = os.path.join(seism_root, 'results/%s/%s/' % (database, exp_name))
    data_rm = os.path.join(seism_root, 'datasets/%s/%s/' % (database, exp_name))
    os.system("rm -rf %s" % (result_rm))
    os.system("rm -rf %s" % (data_rm))
    print('Finished cleanup ...')

    return eval_dict


if __name__ == '__main__':
    import time

    time0 = time.time()
    prediction_path = 'somepath'
    exp_name = 'version_1'.replace('-', '')
    exp_name = 'tmp_' + exp_name
    print('exp name: {}'.format(exp_name))
    eval_edge_predictions_forward(prediction_path, exp_name)

    time1 = time.time()
    print('total time: {}'.format(time1 - time0))
    print('exp name: {}'.format(exp_name))