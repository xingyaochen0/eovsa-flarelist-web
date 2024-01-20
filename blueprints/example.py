import numpy  as np
import pandas as pd
from datetime import timedelta
from flask import Flask, Blueprint, render_template, request, jsonify
import random
import plotly.express as px
import os


example = Blueprint('example', __name__, template_folder='templates')


def get_eo_flare_list(start_utc, end_utc):
    """
    info from EOVSA_flare_list_from_wiki.csv
    """
    file_path = '/data1/xychen/flaskenv/EOVSA_flare_list_from_wiki.csv'#/data1/xychen/flaskenv/EOVSA_flare_list_from_wiki.csv
    df = pd.read_csv(file_path)

    flare_id = df['Flare_ID']
    # dates = df['Date']
    # times = df['Time (UT)']
    EO_tstart=df['EO_tstart']
    # EO_tpeak=df['EO_tpeak']
    EO_tend=df['EO_tend']
    GOES_class = df['flare_class']
    EO_xcen = df['EO_xcen']
    EO_ycen = df['EO_ycen']

    EO_tst_dt = pd.to_datetime(EO_tstart)
    EO_ted_dt = pd.to_datetime(EO_tend)
    t_st = pd.to_datetime(start_utc)
    t_ed = pd.to_datetime(end_utc)

    ind = np.where((EO_tst_dt <= t_ed) & (t_st <= EO_ted_dt))[0]

    result=[]
    keys=['_id','start','end','link']
    keys=['_id','flare_id','start','end','GOES_class','link_dspec_data','link_movie','link_fits']
    if ind.size > 0:
        for i, j in enumerate(ind):

            flare_id_str=str(flare_id[j])

            link_dspec_str = ''##?
            link_dspec_data_str = f'http://ovsa.njit.edu/events/{flare_id_str[0:4]}/'#EOVSA_{flare_id_str[0:4]}_??flare.dat
            link_movie_str = f'http://ovsa.njit.edu/SynopticImg/eovsamedia/eovsa-browser/{flare_id_str[0:4]}/{flare_id_str[4:6]}/{flare_id_str[6:8]}/eovsa.lev1_mbd_12s.flare_id_{flare_id_str}.mp4'
            link_fits_str = f'http://ovsa.njit.edu/fits/flares/{flare_id_str[0:4]}/{flare_id_str[4:6]}/{flare_id_str[6:8]}/{flare_id_str}/'

            result.append({'_id': i,
                'flare_id':int(flare_id[j]),
                'start':EO_tstart[j],
                'end':EO_tend[j],
                'GOES_class':GOES_class[j],
                'link_dspec_data':'<a href="'+link_dspec_data_str+'">DSpec_Data</a>',
                'link_movie':'<a href="'+link_movie_str+'">QL_Movie</a>',
                'link_fits':'<a href="'+link_fits_str+'">FITS</a>'
                })
    return result



def get_eo_dspec(start_utc, end_utc):
    """
    return the tim_plt, freq_plt, spec_plt
    """
    from astropy.io import fits
    from astropy.time import Time
    import os
    import pandas as pd

    t_st = pd.to_datetime(start_utc)
    t_ed = pd.to_datetime(end_utc)

    dates = pd.date_range(t_st, t_ed)

    all_times_isot = []
    all_specs = []

    for date in dates:
        year, month, day = f"{date.year:04d}", f"{date.month:02d}", f"{date.day:02d}"
        # year, month, day = str(t_st.year), '{:02d}'.format(t_st.month), '{:02d}'.format(t_st.day)

        file_path = os.path.join('/data1/eovsa/fits/synoptic/',year, month, day)
        file_name = 'EOVSA_TPall_' + year + month + day + '.fts'


        ##=========================
        try:
            spec_fits = fits.open(os.path.join(file_path,file_name))
            # spec_fits.info()

            spec = spec_fits['PRIMARY'].data
            freq_tp = spec_fits['SFREQ'].data
            time_tp = spec_fits['UT'].data

            freq = [(freq_tp[i])[0] for i in range(len(freq_tp))]
            time = [(time_tp[i])[0]+(time_tp[i])[1]/(86400*1000) for i in range(len(time_tp))]

            freq = np.array(freq)*1e9
            time = Time(time,format='mjd')

            ##=========================
            t_st_mjd = Time(t_st.strftime('%Y-%m-%dT%H:%M:%S')).mjd
            t_ed_mjd = Time(t_ed.strftime('%Y-%m-%dT%H:%M:%S')).mjd
            timerange = [Time(max(t_st_mjd, time[0].mjd), format='mjd'), Time(min(t_ed_mjd, time[-1].mjd), format='mjd')]
            # timerange = [t_st.strftime('%Y-%m-%dT%H:%M:%S'), t_ed.strftime('%Y-%m-%dT%H:%M:%S')]
            # timerange = Time(timerange)

            tidx = np.where((time >= timerange[0]) & (time <= timerange[1]))[0]

            freqrange = [1,18]#in GHz
            fidx = np.where((freq >= freqrange[0] * 1e9) & (freq <= freqrange[1] * 1e9))[0]

            ##=========================
            tim_plt_mjd=(time)[tidx[0]:tidx[-1]]
            # tim_plt = (time.plot_date)[tidx[0]:tidx[-1]]
            freq_plt = (freq/1e9)[fidx[0]:fidx[-1]]
            spec_plt = spec[fidx[0]:fidx[-1],tidx[0]:tidx[-1]]
            tim_plt_isot = (time.isot)[tidx[0]:tidx[-1]]

            spec_plt = [spec_plt[i,:]-np.mean(spec_plt[i,0:5]) for i in range(len(freq_plt))]#tidx[0]-2
            spec_plt = np.array(spec_plt)

            ##=========================
            all_times_isot.append(tim_plt_mjd)
            all_specs.append(spec_plt)

            spec_fits.close()

        except FileNotFoundError:
            print(f"File {file_name} not found. Skipping to next file.")
            continue


    tim_plt_isot = Time(np.concatenate(all_times_isot)).isot
    spec_plt = np.concatenate(all_specs, axis=1)
    ##=========================
    # spec_data=[('tim_plt', tim_plt), ('freq_plt', freq_plt), ('spec_plt', spec_plt)]
    # spec_data = {'tim_plt': tim_plt.tolist(), 'freq_plt': freq_plt.tolist(), 'spec_plt': spec_plt.tolist(), 'tim_plt_isot':tim_plt_isot.tolist()}
    spec_data = {'tim_plt_isot':tim_plt_isot.tolist(), 'freq_plt': freq_plt.tolist(), 'spec_plt': spec_plt.tolist()}

    return spec_data





# @example.route("/api/flare/query", methods=['POST'])
# def get_flare_list_from_database():
#     start = request.form['start']
#     end = request.form['end']
    
#     result = get_eo_flare_list(start, end)

#     spec_data = get_eo_dspec(start, end)

#     tim_plt, freq_plt, spec_plt = spec_data['tim_plt'], spec_data['freq_plt'], spec_data['spec_plt']
    
#     # Create Plotly plot
#     fig = px.imshow(spec_plt, x=tim_plt, y=freq_plt, aspect='auto', origin='lower')

#     # Convert the Plotly figure to HTML
#     plot_html = fig.to_html(full_html=False)

#     # Include the plot HTML in the spec_data dictionary
#     spec_data['plot_html'] = plot_html

#     # return jsonify({"result": result, "spec_data": spec_data})
#     return render_template('index.html', result=result, spec_data=spec_data)



@example.route("/api/flare/query", methods=['POST'])
def get_flare_list_from_database():
    try:
        start = request.form['start']
        end = request.form['end']
        if not start or not end:
            raise ValueError("Start and end times are required.")
        
        result = get_eo_flare_list(start, end)
        spec_data = get_eo_dspec(start, end)

        if not result:
            raise ValueError("No flare data found for the specified time range.")


        # tim_plt, freq_plt, spec_plt, tim_plt_isot = spec_data['tim_plt'], spec_data['freq_plt'], spec_data['spec_plt'], spec_data['tim_plt_isot']
        tim_plt_isot, freq_plt, spec_plt = spec_data['tim_plt_isot'], spec_data['freq_plt'], spec_data['spec_plt']

        # fig = px.imshow(spec_plt, x=tim_plt, y=freq_plt, aspect='auto', origin='lower')
        spec_plt_array = np.array(spec_plt)
        spec_plt_log = np.where(spec_plt_array <= 0, 1e-10, spec_plt_array)
        spec_plt_log = np.log10(spec_plt_log)

        tim_plt_datetime = pd.to_datetime(tim_plt_isot)
        fig = px.imshow(spec_plt_log, x=tim_plt_datetime, y=freq_plt,
            zmin=0., zmax=0.8, aspect='auto', origin='lower')
            # zmin=np.min(spec_plt_log), zmax=np.max(spec_plt_log), aspect='auto', origin='lower')
        fig.update_xaxes(tickformat='%H:%M')
        fig.update_layout(
            xaxis_title="Time",  # Replace with your actual x-axis title
            yaxis_title="Frequency [GHz]",  # Replace with your actual y-axis title
            coloraxis_colorbar=dict(title="log10 Flux [sfu]"))

        plot_html = fig.to_html(full_html=False)
        print('Data success.....')

        return jsonify({"result": result, "plot_html": plot_html})

    except Exception as e:
        # Log the exception for debugging
        print(f"Error: {e}")
        # Return a JSON response with the error message
        return jsonify({"error": str(e)}), 500


#route example
@example.route("/")
def render_example_paper():
    return render_template('index.html', result=[], plot_html=None)



# @example.route("/plot", methods=['POST'])
# def render_plot():
#     start = request.form['start']
#     end = request.form['end']

#     # Create an array for plotting based on the provided start and end times

#     spec_data = get_eo_dspec(start, end)
#     # tim_plt, freq_plt, spec_plt = spec_data[0][1], spec_data[1][1], spec_data[2][1]
#     tim_plt, freq_plt, spec_plt = spec_data['tim_plt'], spec_data['freq_plt'], spec_data['spec_plt']

#     # fig = px.pcolormesh(tim_plt, freq_plt, spec_plt, cmap='jet')
#     fig = px.imshow(spec_plt, x=tim_plt, y=freq_plt, aspect='auto', origin='lower')

#     # Convert the Plotly figure to HTML
#     plot_html = fig.to_html(full_html=False)

#     return render_template('plot.html', plot_html=plot_html)






# @example.route("/api/flare/query", methods=['POST'])
# def get_flare_list_from_database():
#     start = request.form['start']
#     end = request.form['end']
#     """
#         add your python code to query database here
#     """
#     result = get_eo_flare_list(start,end)

#     return jsonify(result)


