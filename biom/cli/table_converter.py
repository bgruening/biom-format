# -----------------------------------------------------------------------------
# Copyright (c) 2011-2015, The BIOM Format Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

table_types = ["OTU table",
               "Pathway table",
               "Function table",
               "Ortholog table",
               "Gene table",
               "Metabolite table",
               "Taxon table",
               "Table"]

observation_metadata_types = {
    'sc_separated': lambda x: [e.strip() for e in x.split(';')],
    'naive': lambda x: x
}
observation_metadata_types['taxonomy'] = \
    observation_metadata_types['sc_separated']

observation_metadata_formatters = {
    'sc_separated': lambda x: '; '.join(x),
    'naive': lambda x: x
}


def convert(table, sample_metadata, observation_metadata,
            to_json, to_hdf5, to_tsv, collapsed_samples,
            collapsed_observations, header_key, output_metadata_id, table_type,
            process_obs_metadata, tsv_metadata_formatter):

    if sum([to_tsv, to_hdf5, to_json]) == 0:
        raise ValueError("Must specify an output format")
    elif sum([to_tsv, to_hdf5, to_json]) > 1:
        raise ValueError("Can only specify a single output format")

    table.type = table_type
    if tsv_metadata_formatter is not None:
        obs_md_fmt_f = observation_metadata_formatters[tsv_metadata_formatter]

    if sample_metadata is not None:
        table.add_metadata(sample_metadata)

    # if the user does not specify a name for the output metadata column,
    # set it to the same as the header key
    output_metadata_id = output_metadata_id or header_key

    if process_obs_metadata is not None and not to_tsv:
        if table.metadata(axis='observation') is None:
            raise ValueError("Observation metadata processing requested "
                             "but it doesn't appear that there is any "
                             "metadata to operate on!")

        # and if this came in as TSV, then we expect only a single type of
        # metadata
        md_key = table.metadata(axis='observation')[0].keys()[0]

        process_f = observation_metadata_types[process_obs_metadata]
        it = zip(table.ids(axis='observation'),
                 table.metadata(axis='observation'))
        new_md = {id_: {md_key: process_f(md[md_key])} for id_, md in it}

        if observation_metadata:
            for k, v in observation_metadata.items():
                new_md[k].update(v)
        table.add_metadata(new_md, 'observation')

    if to_tsv:
        result = table.to_tsv(header_key=header_key,
                              header_value=output_metadata_id,
                              metadata_formatter=obs_md_fmt_f)
    elif to_json:
        result = table
    elif to_hdf5:
        result = table
        if collapsed_observations:
            metadata = [{'collapsed_ids': md.keys()}
                        for md in result.metadata(axis='observation')]
            result._observation_metadata = metadata
        if collapsed_samples:
            metadata = [{'collapsed_ids': md.keys()}
                        for md in result.metadata()]
            result._sample_metadata = metadata
        if collapsed_observations or collapsed_samples:
            # We have changed the metadata, it is safer to make sure that
            # it is correct
            result._cast_metadata()

    return result