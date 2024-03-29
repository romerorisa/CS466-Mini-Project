from random import random
import numpy as np
import os
from Bio import SeqIO
import math
import timeit
from generate import convert_motif


def find_best_pos(sequence, motif, background, ML):
    """Scores the substrings in a sequence and returns the position of the substring selected by the softmax of all the scores

    Args:
        sequence (array): a 1d array of A, C, G, and Ts
        motif (array): a 2d array representing a PWM
        background (array): 2d array representing the background information of A, C, G, and T
        ML (int): motif length

    Returns:
        np.random.choice(len(sequence)-ML+1, p=scores): a selected integer representing the substring index based on the score probability distribution
    """
    nuc_dict = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
    scores = np.zeros(len(sequence)-ML+1)
    for i in range(len(sequence)-ML+1):
        score = 0
        for j in range(i, i+ML):
            nuc = nuc_dict[sequence[j]]
            if motif[j-i, nuc] == 0 or background[nuc] == 0:
                score = 0
                break
            score += math.log(motif[j-i, nuc]/background[nuc])
        scores[i] = score
    if np.sum(np.exp(scores)) == 0:
        return np.random.choice(len(sequence)-ML+1)
    scores = np.exp(scores)/np.sum(np.exp(scores))
    return np.random.choice(len(sequence)-ML+1, p=scores)

def gibbs_find_motif(sequence_strs, ML):
    """Gibbs sampling algorithm to find the motif

    Args:
        sequence_strs (array of strings): all the sequences in a fasta file
        ML (int): motif length

    Returns:
        motif/sequences.shape[1](array): the predicted PWM 
        sequence_pos(array): an array of sites(integers)
        (stop-start)(float): runtime of algorithm
    """
    start = timeit.default_timer()
    sequence_list = np.array([[i for i in x] for x in sequence_strs])
    background = np.zeros((sequence_list.shape[0], 4))
    background[:,0] = np.count_nonzero(sequence_list=="A", axis=1)
    background[:,1] = np.count_nonzero(sequence_list=="C", axis=1)
    background[:,2] = np.count_nonzero(sequence_list=="G", axis=1)
    background[:,3] = np.count_nonzero(sequence_list=="T", axis=1)
    background = background/sequence_list.shape[1]
    sequence_pos = np.random.randint(0, sequence_list.shape[1]-ML+1, (sequence_list.shape[0]))
    prev_sequence_pos = np.full_like(sequence_pos, -1)
    motif = np.zeros((ML, 4))
    count = 0 
    while not np.array_equal(prev_sequence_pos, sequence_pos) and count < 2000:
        count += 1
        prev_sequence_pos = np.copy(sequence_pos)
        for i in range(sequence_list.shape[0]):
            idxs = ((np.arange(0, ML, dtype=np.int64) + np.zeros((sequence_list.shape[0],1), dtype=np.int64)) + sequence_pos[:, None])
            idxs = idxs + np.repeat(np.arange(0,sequence_list.shape[0]*sequence_list.shape[1], sequence_list.shape[1]), ML, axis=0).reshape(-1,ML)
            sequences = sequence_list.flatten()[idxs].reshape(-1, ML)
            sequences = np.vstack((sequences[:i] ,sequences[i+1:])).T
            motif[:,0] = np.count_nonzero(sequences=="A", axis=1)
            motif[:,1] = np.count_nonzero(sequences=="C", axis=1)
            motif[:,2] = np.count_nonzero(sequences=="G", axis=1)
            motif[:,3] = np.count_nonzero(sequences=="T", axis=1)
            motif = motif/sequences.shape[1]
            sequence_pos[i] = find_best_pos(sequence_list[i], motif, background[i], ML)
    idxs = ((np.arange(0, ML, dtype=np.int64) + np.zeros((sequence_list.shape[0],1), dtype=np.int64)) + sequence_pos[:, None])
    idxs = idxs + np.repeat(np.arange(0,sequence_list.shape[0]*sequence_list.shape[1], sequence_list.shape[1]), ML, axis=0).reshape(-1,ML)
    sequences = sequence_list.flatten()[idxs].reshape(-1, ML).T
    motif[:,0] = np.count_nonzero(sequences=="A", axis=1)
    motif[:,1] = np.count_nonzero(sequences=="C", axis=1)
    motif[:,2] = np.count_nonzero(sequences=="G", axis=1)
    motif[:,3] = np.count_nonzero(sequences=="T", axis=1)
    stop = timeit.default_timer()
    print(count)
    return motif/sequences.shape[1], sequence_pos, (stop-start)

if __name__ == "__main__":


    for x in os.scandir('dataset'):
        if x.path.startswith('dataset\\SC'):
            for i in range(1, 11):
                f = open(os.path.join(x.path, str(i), 'sequences.fasta'), 'r')
                g = open(os.path.join(x.path, str(i), 'motiflength.txt'), 'r')
                ML = int(g.readline())
                fasta_sequences = SeqIO.parse(f,'fasta')
                sequence_strs = []
                for fasta in fasta_sequences:
                    sequence_strs.append(str(fasta.seq))
                motif, sites, time = gibbs_find_motif(sequence_strs, ML)
                convert_motif(ML, motif, os.path.join(x.path, str(i), 'predictedmotif.txt'))
                k = open(os.path.join(x.path, str(i), 'predictedsites.txt'), 'w')
                j = open(os.path.join(x.path, str(i), 'runtime.txt'), 'w')
                site_strs = [str(i) + '\n' for i in sites]
                site_strs[-1] = str(sites[-1])
                k.writelines(site_strs)
                j.write(str(time))
                print(x.path, i)
                print(motif)
                f.close()
                g.close()
                k.close()
                j.close()

