# -*- coding: latin-1 -*-

"""
Prophtools: Tools for heterogenoeus network prioritization.

Copyright (C) 2016 Carmen Navarro Luzón <cnluzon@decsai.ugr.es>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

 .. module :: run.py
 .. moduleauthor :: C. Navarro Luzón <cnluzon@decsai.ugr.es>

 Runs a Prioritization query on sample data or a provided matrix file.

"""
import prophtools.common.method as method
import prophtools.common.graphdata as graphdata
import prophtools.utils.validation as validation

from prophtools.utils.experiment import Experiment

import os


class LocalRunExperiment(Experiment):
    """
    Experiment for running a local instance of the prioritizationmethod.
    """
    def _print_help(self):
        help_message = """
ProphTools prioritize: Run a local prioritization experiment on a network
configuration.

Required parameters:
    matfile: mat file containing the networks and their configuration (see
             ProphTools documentation for more info on this format.)
    src    : Source network (as an index)
    dst    : Destination network (as an index)
    query  : Comma-separated list of indexes that are on the query target.

Optional parameters:
    corr_function: Correlation function used to compute the score at end
                   of the prioritization. Available functions are pearson and
                   spearman correlation. Default (pearson).
        """
        print(help_message)

    def _run_prioritizer(self, prioritizer, idx_query, origin, destination,
                         method="prophnet", corr_function="pearson"):
        """
        A helper method for the experiment routine.
        """
        num_results = 10
        self._start_profiling()
        results = prioritizer.propagate(idx_query,
                                        origin,
                                        destination,
                                        corr_function)

        stats = self._end_profiling()

        top_results = min(len(results), num_results)
        sorted_results = sorted(results, key=lambda x: x[0], reverse=True)

        self._print_formatted_results(sorted_results, method, top_results)
        
    def _print_formatted_results(self, results, method, max_results):
        print "Entity\tScore"
        for i in range(max_results):
            result_entity = results[i][1]
            result_score = results[i][0]

            result_str = '{}\t{:8.4f}'.format(result_entity, result_score)
            print result_str

    def _load_parameters(self, section):
        params = {}
        params['data_path'] = self.config.get(section, 'data_path')
        params['src'] = int(self.config.get(section, 'src'))
        params['dst'] = int(self.config.get(section, 'dst'))
        params['matfile'] = self.config.get(section, 'matfile')
        params['corr_function'] = self.config.get(section, 'corr_function')
        params['query'] = self.config.get(section, 'query')
        return params

    def experiment(self, extra_params):
        """
        Run the experiment. All config overriding and stuff are performed
        in the Experiment class.
        """
        self.log.info("Running Prioritization.")
        self.log.info("Parsing parameters from config file.")
        required = ['matfile', 'src', 'dst', 'query']

        if self._are_required_parameters_valid(self.config, required):
            cfg_params = self._load_parameters("run")

            self.log.info("Loading data.")

            propagation_data = None
            matfile_path = os.path.join(cfg_params['data_path'],
                                        cfg_params['matfile'])

            if validation.check_file_exists(matfile_path, self.log):
                propagation_data = graphdata.GraphDataSet.read(
                    cfg_params['data_path'],
                    cfg_params['matfile'])
            else:
                msg = "Could not open matfile {}. Exiting.".format(matfile_path)
                self.log.error(msg)
                return -1
            
            query_vector = cfg_params['query'].split(',')
            query_vector = [int(q) for q in query_vector]

            self.log.info("Prioritizing.")

            prioritizer = method.ProphNet(propagation_data)

            self._run_prioritizer(prioritizer, query_vector,
                                  cfg_params['src'],
                                  cfg_params['dst'],
                                  corr_function=cfg_params['corr_function'])

            self.log.info("Experiment run successfully.")
        else:
            self._print_help()