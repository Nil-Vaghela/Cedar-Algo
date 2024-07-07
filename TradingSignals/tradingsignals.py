import requests

class GetTradingSignals():
    def TradingSignals():
        url = "https://www.cedaralgo.in/api/trading_signals"
        trading_data = {}
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            
            # Process the JSON data if the request was successful
            trading_signals = response.json()

            if trading_signals:
        # Organize data by indexName
                
                for signal in trading_signals:
                    index_name = signal['indexName']
                    if index_name in trading_data:
                        trading_data[index_name].append(signal)
                    else:
                        trading_data[index_name] = [signal]
            else:
                trading_data = None
            return trading_data
        
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)