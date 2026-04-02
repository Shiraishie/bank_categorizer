# bank_categorizer

Project because i'm hella bored. Uses llms to categorize bank transactions in SG, since we cant access merchant code of each transactions (shuld be private info for banks)
categorizes food paynow transactions as food, and transfers out as paynow out and transfers in as paynow in.

### Flow

![alt text](./media/image.png)

### To use

create own .env file
will add support for using own api key eventually~

```bash
GROQ_API_KEY='gskxxxxxx'
```

open terminal and run

```bash
streamlit run streamlit.py
```

### gif

![](./media/giff2.gif)

### Thanks

to the developers of monopoly!!
