#!/usr/bin/env python3
"""Reconstruct the exact supplied ZIP from its lossless XZ storage wrapper."""
import argparse
import hashlib
import lzma
from pathlib import Path

ORIGINAL_NAME = 'CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip'
ORIGINAL_SHA256 = 'c07b3256e8f5f07a953b98b8299efeae0f21fb85e511614910b9b29cece461b2'
ORIGINAL_BYTES = 12923350
WRAPPER_BYTES = 10865144
WRAPPER_SHA256 = 'c6e2454192d32f86e275a80183c8824084e5dc463a261fcbefbbbf806a141af2'


def restore(wrapper, output):
    stored = Path(wrapper).read_bytes()
    if len(stored) != WRAPPER_BYTES or hashlib.sha256(stored).hexdigest() != WRAPPER_SHA256:
        raise ValueError('Wrapper identity differs / Identité de l’enveloppe différente')
    data = lzma.decompress(stored)
    if len(data) != ORIGINAL_BYTES or hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('Original ZIP identity differs / Identité du ZIP original différente')
    # Exclusive creation refuses existing files and symlinks without truncation.
    with Path(output).open('xb') as stream:
        stream.write(data)
    return ORIGINAL_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(ORIGINAL_NAME),
                        help='New ZIP path; never overwrite / Nouveau chemin ZIP; aucun écrasement')
    args = parser.parse_args()
    wrapper = Path(__file__).resolve().parents[1] / 'docs/masterclass-101' / (ORIGINAL_NAME + '.xz')
    try:
        digest = restore(wrapper, args.output)
    except (OSError, ValueError, lzma.LZMAError) as error:
        parser.exit(1, 'Restore failed / Échec de restauration: ' + str(error) + '\n')
    print('Original ZIP restored and verified / ZIP original restauré et vérifié: ' + digest)


if __name__ == '__main__':
    main()
