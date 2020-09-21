#!/usr/bin/python3

from flask import Flask, render_template, request
import requests # For making the external API calls
import os
def create_app():
    app = Flask( __name__ , instance_relative_config=True)
    app.config.from_pyfile(os.path.join(app.instance_path, 'config.py'), silent=False)

    def search_bulk_ids( targets, scope ):
        '''Get Character IDs in bulk'''
        '''Targets=list of characters/corps/alliances. Scope="characters", "corporations", or "alliances"'''
        bulkSearchURL = 'https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en-us'
        # Strip out duplicates because the API shits itself
        targets = list( dict.fromkeys( targets ) )
        print(targets)
        try:
            return requests.post(bulkSearchURL,json=targets).json()[scope]
        except KeyError: #No characters passed, or ALL are invalid names
            return []

    def get_info( scope, target ):
        '''Scope is characters, corporations, or alliances'''
        requestURL = 'https://esi.evetech.net/latest/%s/%s/?datasource=tranquility' % (scope, target)
        return requests.get( requestURL ).json()

    def listify_corpse_input( corpse_input ):
        app.logger.debug( '-'*20 + 'Corpse Input:' )
        app.logger.debug( corpse_input )
        corpse_list = corpse_input.replace('\'s Frozen Corpse','').replace('Biomass','').replace('2 m3\t','').replace('\t','').split('\r\n')
        app.logger.debug( '-' * 20 + 'Corpse List:' )
        app.logger.debug( corpse_list )
        return corpse_list

    @app.route( '/' )
    def corpses():
        return  render_template( 'corpses.html' )

    @app.route('/result',methods = ['POST', 'GET'])
    def result():
        if request.method == 'POST':
            raw = request.form['Corpses']
            # Check if no corpses were entered.
            if raw == '':
                return render_template( 'result.html', result = [{'name':'You forgot', 'corp':'the damn corpses', 'alliance':'you infantile pillock!'}] )
            else:
                chars = listify_corpse_input( raw )
            while ( '' in chars ): # Remove empty lines. (if line0 is empty it returns nothing!)
                chars.remove('')
            chars = search_bulk_ids( chars, 'characters' )
            app.logger.debug( chars )
            for char in chars:
                app.logger.debug( char )
                charinfo = get_info( 'characters', char['id'])
                char['corp_id'] = charinfo[ 'corporation_id' ]
                corpinfo = get_info( 'corporations', char[ 'corp_id' ] )
                char['corp'] = corpinfo[ 'name' ]
                try: # Not everyone is in an alliance
                    char['alliance_id'] = charinfo[ 'alliance_id' ]
                    allianceinfo = get_info( 'alliances', char[ 'alliance_id' ] )
                    char['alliance'] = allianceinfo[ 'name' ]
                except KeyError:
                    char['alliance_id'], char['alliance'] = '',''
            return render_template( "result.html" ,result = chars  )
    return app

#if __name__ == '__main__': app.run( debug = True )
