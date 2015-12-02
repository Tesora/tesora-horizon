/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
(function() {
  'use strict';

  describe('horizon.framework.widgets.headers', function() {
    it('should exist', function() {
      expect(angular.module('horizon.framework.widgets.headers')).toBeDefined();
    });
  });

  describe('horizon.framework.widgets.headers.basePath', function () {
    var headersBasePath, staticUrl;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.headers'));
    beforeEach(inject(function ($injector) {
      headersBasePath = $injector.get('horizon.framework.widgets.headers.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
    }));

    it('should be defined', function () {
      expect(headersBasePath).toBeDefined();
    });

    it('should get set correctly', function () {
      expect(headersBasePath).toEqual(staticUrl + 'framework/widgets/headers/');
    });
  });

})();
