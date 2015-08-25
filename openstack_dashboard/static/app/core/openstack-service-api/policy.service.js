/**
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.policy', PolicyService);

  PolicyService.$inject = ['horizon.framework.util.http.service',
                           'horizon.framework.widgets.toast.service'];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.policy
   * @description Provides a direct pass through to the policy engine in
   * Horizon.
   */
  function PolicyService(apiService, toastService) {
    var service = {
      check: check
    };

    return service;

    /**
     * @name horizon.app.core.openstack-service-api.policy.check
     * @description
     * Check the passed in policy rule list to determine if the user has
     * permission to perform the actions specified by the rules. The service
     * APIs will ultimately reject actions that are not permitted. This is used
     * for Role Based Access Control in the UI only. The required parameter
     * should have the following structure:
     *
     *   {
     *     "rules": [
     *                [ "compute", "compute:get_all" ],
     *              ],
     *     "target": {
     *                 "project_id": "1"
     *               }
     *   }
     *
     * where "rules" is a list of rules (1 or greater in length) policy rules
     * which are composed of a
     *    * service name -- maps the policy rule to a service
     *    * rule -- the policy rule to check
     * and "target" key and value is optional. In some cases, policy rules
     * require specific details about the object that is to be acted on.
     * If added, it is merely a dictionary of keys and values.
     *
     *
     * The following is the response if the check passes:
     *   {
     *     "allowed": true
     *   }
     *
     * The following is the response if the check fails:
     *   {
     *     "allowed": false
     *   }
     */
    function check(policyRules) {
      return apiService.post('/api/policy/', policyRules)
        .error(function() {
          toastService.add('warning', gettext('Policy check failed.'));
        });
    }
  }
}());
