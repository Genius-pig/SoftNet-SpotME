import numpy as np
import pandas as pd


def load_excel(dataset_name):
    if dataset_name == 'CASME_sq':
        xl = pd.ExcelFile(dataset_name + '/code_final.xlsx')  # Specify directory of excel file

        cols_name = ['subject', 'video', 'onset', 'apex', 'offset', 'au', 'emotion', 'type', 'selfReport']
        code_final = xl.parse(xl.sheet_names[0], header=None, names=cols_name)  # Get data

        video_names = []
        for videoName in code_final.iloc[:, 1]:
            video_names.append(videoName.split('_')[0])
        code_final['videoName'] = video_names

        naming1 = xl.parse(xl.sheet_names[2], header=None, converters={0: str})
        dict_video_name = dict(zip(naming1.iloc[:, 1], naming1.iloc[:, 0]))
        code_final['videoCode'] = [dict_video_name[i] for i in code_final['videoName']]

        naming2 = xl.parse(xl.sheet_names[1], header=None)
        dictSubject = dict(zip(naming2.iloc[:, 2], naming2.iloc[:, 1]))
        code_final['subjectCode'] = [dictSubject[i] for i in code_final['subject']]

    elif dataset_name == 'SAMMLV':
        xl = pd.ExcelFile(dataset_name + '/SAMM_LongVideos_V2_Release.xlsx')

        cols_name = ['Subject', 'Filename', 'Inducement Code', 'Onset', 'Apex', 'Offset', 'Duration', 'Type',
                    'Action Units', 'Notes']
        code_final = xl.parse(xl.sheet_names[0], header=None, names=cols_name, skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        video_names = []
        subject_name = []
        for videoName in code_final.iloc[:, 1]:
            video_names.append(str(videoName).split('_')[0] + '_' + str(videoName).split('_')[1])
            subject_name.append(str(videoName).split('_')[0])
        code_final['videoCode'] = video_names
        code_final['subjectCode'] = subject_name
        # Synchronize the columns name with CAS(ME)^2
        code_final.rename(columns={'Type': 'type', 'Onset': 'onset', 'Offset': 'offset', 'Apex': 'apex'}, inplace=True)
        print('Data Columns:', code_final.columns)  # Final data column
    return code_final


def load_gt(dataset_name, expression_type, images, subjects_videos, subjects, code_final):
    dataset_expression_type = expression_type
    if dataset_name == 'SAMMLV' and expression_type == 'micro-expression':
        dataset_expression_type = 'Micro - 1/2'
    elif dataset_name == 'SAMMLV' and expression_type == 'macro-expression':
        dataset_expression_type = 'Macro'

    vid_need = []
    vid_count = 0
    ground_truth = []
    for sub_video_each_index, sub_vid_each in enumerate(subjects_videos):
        ground_truth.append([])
        for videoIndex, videoCode in enumerate(sub_vid_each):
            on_off = []
            for i, row in code_final.iterrows():
                if row['subjectCode'] == subjects[sub_video_each_index]:  # S15, S16... for CAS(ME)^2, 001, 002... for SAMMLV
                    if row['videoCode'] == videoCode:
                        if row['type'] == dataset_expression_type:  # Micro-expression or macro-expression
                            if row['offset'] == 0:  # Take apex if offset is 0
                                on_off.append([int(row['onset'] - 1), int(row['apex'] - 1)])
                            else:
                                if (dataset_expression_type != 'Macro' or int(
                                        row['onset']) != 0):  # Ignore the samples that is extremely long in SAMMLV
                                    on_off.append([int(row['onset'] - 1), int(row['offset'] - 1)])
            if len(on_off) > 0:
                vid_need.append(vid_count)  # To get the video that is needed
            ground_truth[-1].append(on_off)
            vid_count += 1

    # Remove unused video
    final_samples = []
    final_videos = []
    final_subjects = []
    count = 0
    for subjectIndex, subject in enumerate(ground_truth):
        final_samples.append([])
        final_videos.append([])
        for samplesIndex, samples in enumerate(subject):
            if count in vid_need:
                final_samples[-1].append(samples)
                final_videos[-1].append(subjects_videos[subjectIndex][samplesIndex])
                final_subjects.append(subjects[subjectIndex])
            count += 1

    # Remove the empty data in array
    final_subjects = np.unique(final_subjects)
    final_videos = [ele for ele in final_videos if ele != []]
    final_samples = [ele for ele in final_samples if ele != []]
    final_images = [images[i] for i in vid_need]
    print('Total Videos:', len(final_images))
    return final_images, final_videos, final_subjects, final_samples


def cal_k(dataset_name, expression_type, final_samples):
    samples = [samples for subjects in final_samples for videos in subjects for samples in videos]
    total_duration = 0
    for sample in samples:
        total_duration += sample[1] - sample[0]
    N = total_duration / len(samples)
    k = int((N + 1) / 2)
    print('k (Half of average length of expression) =', k)
    return k
