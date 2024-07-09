import requests
import re  # Import regex module

class GetTradingSignals:
    @staticmethod
    def TradingSignals():
        url = "https://www.cedaralgo.in/api/trading_signals"
        trading_data = {}
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            
            # Process the JSON data if the request was successful
            trading_signals = response.json()

            if trading_signals:
                for signal in trading_signals:
                    index_name = signal['indexName']
                    # Regex to extract the strike price and the type (PE or CE) by skipping the first two digits
                    match = re.search(r'\d{2}(\d+)(PE|CE)', signal['name'])
                    if match:
                        formatted_name = f"{match.group(1)} {match.group(2)}"  # Format like '24450 PE'
                        signal['name'] = formatted_name  # Update the name in the signal

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
            print("Oops: Something Else", err)